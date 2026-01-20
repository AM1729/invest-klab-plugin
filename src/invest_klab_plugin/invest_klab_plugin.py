import logging
import os

## Natcap Imports
from natcap.invest import validation
from natcap.invest import utils
from natcap.invest.unit_registry import u
from natcap.invest import gettext
from natcap.invest import spec


## klab Imports
from klab.klab import Klab
from klab.geometry import GeometryBuilder
from klab.observable import Observable
from klab.utils import Export, ExportFormat

import asyncio
import os
from shapely import wkt
import geopandas as gpd

LOGGER = logging.getLogger(__name__)
STANDARD_PATH = os.path.join(os.path.expanduser('~'), ".klab", "testcredentials.properties")

MODEL_SPEC = spec.ModelSpec(
    model_id="klab",
    model_title=gettext("klab Plugin"),
    module_name=__name__,
    userguide='https://github.com/AM1729/invest-klab-plugin/blob/main/README.md',
    input_field_order=[
        ['workspace_dir', 'results_suffix'],
        ['kim_semantic_query'],
        ['spatial_context'],
        ['year'],
        ['klab_certificate_path']],

    inputs=[
        spec.WORKSPACE,
        spec.SUFFIX,
        spec.N_WORKERS,

        spec.StringInput(
            id = "klab_certificate_path",
            name = gettext("Klab Certificate Path"),
            about = gettext("Path to the klab certificate file")
        ),

        spec.DirectoryInput(
            id="workspace_dir",
            name=gettext("workspace"),
            about=gettext(
                "The folder where all the model's output files will be written. If "
                "this folder does not exist, it will be created. If data already "
                "exists in the folder, it will be overwritten."),
            contents=[],
            must_exist=False,
            permissions="rwx"
        ),

       ## spec.StringInput(
       ##     id="klab_engine_url",
       ##     name = gettext("Klab Engine URL"),
       ##     about = gettext(
       ##         "URL of the klab engine to connect to, " \
       ##         "Defaults to Local K.LAB Engine"),
       ## ),

        spec.StringInput(
            id="kim_semantic_query",
            name=gettext("kim semantic query"),
            about=gettext(
                "Semantic Query based on kim, required to query the Klab Semantic Web"
                "of GeoSpatial Data"),
            required=True
        ),

        spec.VectorInput(
            id='spatial_context',
            name='Area of Interest',
            about=gettext(
                'Path to a GDAL polygon vector representing the Area of Interest '
                '(AOI). Coordinates represented by longitude, latitude decimal degrees '
                '(e.g. WGS84).'),
            required=True,
            fields=[],
            geometry_types={'POLYGON', 'MULTIPOLYGON'}
        ),

        spec.StringInput(
            id='year',
            name="Year",
            about=gettext("Year of the observation"),
            required=True
        )
    ],
    outputs=[
        spec.SingleBandRasterOutput(
            id="result",
            path="result.tif",
            about="Generated Raster after k.LAB Resolved the Semantic Query",
            data_type=float,
        )
    ]
)


def execute(args):
    LOGGER.info("Starting k.LAB Plugin Model")
    ##klab_engine_url = args.get('klab_engine_url', 'http://localhost:8080')
    klab_certificate_path = args.get('klab_certificate_path', None)
    year = int(args['year'])
    semantic_query = args['kim_semantic_query']
    spatial_context_wkt = build_spatial_context_wkt(args['spatial_context'])

    LOGGER.info(f" Querying k.LAB Semantic Web with Query: {semantic_query}")

    try:
        klab = get_klab_instance(klab_certificate_path)
        asyncio.run(ARIES_request(
            klab=klab,
            area_WKT=spatial_context_wkt,
            obs_res="1 km",
            obs_year=year,
            observable=semantic_query,
            export_format=ExportFormat.BYTESTREAM,
            export_path=os.path.join(args['workspace_dir'], "result.tif")
        ))

    except Exception as e:
        LOGGER.error(f"An error occurred while executing the k.LAB model: {e}")
        raise e
    
    finally:
        if klab:
            klab.close()

    LOGGER.info('Done!')


@validation.invest_validator
def validate(args, limit_to=None):
    if 'spatial_context' in args:
        try:
            _check_lonlat_coords(args['spatial_context'])
        except ValueError as e:
            raise ValueError('Invalid WKT format for spatial context: ' + str(e))

    if 'year' in args:
        try:
            year = int(args['year'])
            if year < 1900:
                raise ValueError('Year must be 1900 or later')
        except (ValueError, TypeError):
            raise ValueError('Invalid year format')

    return validation.validate(args, MODEL_SPEC)

async def ARIES_request(klab: Klab, area_WKT: str, obs_res: str, obs_year: int, observable: str,
                        export_format: ExportFormat, export_path: str):
    
    # create the semantic type and geometry/time to init the CONTEXT
    obs = Observable.create("earth:Region")
    grid = GeometryBuilder().grid(urn=area_WKT, resolution=obs_res).years(obs_year).build()

    # submit to engine to generate the CONTEXT
    ticketHandler = klab.submit(obs, grid)
    context = await ticketHandler.get()

    dataflow = context.getDataflow(ExportFormat.KDL_CODE)
    provenenace = context.getProvenance(True, ExportFormat.ELK_GRAPH_JSON)


    # define the observable (dataset or model) and submit to context
    obsData = Observable.create(observable)
    ticketHandler = context.submit(obsData)

    data = await ticketHandler.get()

    # retrieve the dataset and export to disk
    data.exportToFile(Export.DATA, export_format, export_path)

    dataflow = context.getDataflow(ExportFormat.KDL_CODE)
    provenenace = context.getProvenance(True, ExportFormat.ELK_GRAPH_JSON)

    print (dataflow)
    print ("===========================")
    print (provenenace)

def get_klab_instance(fpath: str = STANDARD_PATH) -> Klab:
    try:
        print('- try Remote Engine connection ....')
        klab = Klab.create(credentialsFile=fpath)
    except:
        try:
            print('- try Local Engine connection ...')
            klab = Klab.create()
        except:
            raise RuntimeError('Could not establish connection to a k.lab engine')

    if klab and klab.isOnline():
        print(f'* connection to {klab.engine.url} was successfully established. session: {klab.engine.session}')
    else:
        raise EnvironmentError('could not establish connection to the klab instance')

    return klab


def _check_lonlat_coords(vector_path):
    """
    Validates that the AOI vector file uses geographic coordinates 
    (longitude and latitude in decimal degrees). Raises a ValueError if not.
    Works with shapefiles, including zipped shapefiles.
    """    
    gdf = gpd.read_file(vector_path)
    
    if gdf.crs is None:
        raise ValueError(
            "AOI vector file has no spatial reference system defined."
        )

    # Check if CRS is geographic (degrees)
    if not gdf.crs.is_geographic:
        raise ValueError(
            "The AOI vector file must use geographic coordinates (longitude "
            "and latitude in decimal degrees), such as WGS 84 (EPSG:4326). "
            "However, a projected coordinate system was found instead. To "
            "fix this, reproject your vector data to EPSG:4326 (or similar)."
        )
    

def build_spatial_context_wkt(vector_path):
    '''
    Builds a WKT representation of the spatial context from the given vector file.
    Assumes the vector file uses geographic coordinates (longitude and latitude in decimal degrees).
    Returns a string in the format "EPSG:4326 <WKT_GEOMETRY>, which is consumable for k.LAB".
    '''
    gdf = gpd.read_file(vector_path)
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    wkt_geom = gdf.geometry.iloc[0].wkt ## Only one geometry element 
    return f"EPSG:4326 {wkt_geom}"