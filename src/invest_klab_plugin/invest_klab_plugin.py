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
import json
import logging
from shapely import wkt
import geopandas as gpd
from pathlib import Path
from markdownify import markdownify as md

LOGGER = logging.getLogger(__name__)
STANDARD_PATH = os.path.join(os.path.expanduser('~'), ".klab", "credentials.properties")
EARTH_REGION_SEMANTICS = "earth:Region"

MODEL_SPEC = spec.ModelSpec(
    model_id="klab",
    model_title=gettext("klab Plugin"),
    module_name=__name__,
    userguide='https://github.com/integratedmodelling/invest-klab-plugin/blob/main/README.md',
    input_field_order=[
        ['workspace_dir', 'results_suffix'],
        ['kim_semantic_query'],
        ['spatial_context'],
        ['year'],
        ['klab_auth_path']],

    inputs=[
        spec.WORKSPACE,
        spec.SUFFIX,
        spec.N_WORKERS,

        spec.FileInput(
            id = "klab_auth_path",
            name = gettext("Path to your k.LAB Remote Engine Credentials"),
            about = gettext("Path to the credentials File consisting of your Username, Password and Remote Server URL "
            "in case one wants to connect to a Remote Server."
            "Default: Local Engine, http://localhost:8283/modeler")
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
            about=gettext('Path to a GDAL polygon vector representing the Area of Interest (AOI).'),
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
        ),

        spec.FileOutput(
            id='provenance',
            path='provenance.html',
            about=gettext(
                'Exported Provenance of the k.LAB Context in HTML format, including the dataflow and the engine provenance graph')
        )
    ]
)


def execute(args):
    LOGGER.info("Starting k.LAB Plugin Model")
    klab_certificate_path = args.get('klab_auth_path', None)
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
            export_path=os.path.join(args['workspace_dir'], "result.tif"),
            provenance_export_path=os.path.join(args['workspace_dir'], "provenance.html")
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
                        export_format: ExportFormat, export_path: str, provenance_export_path: str = None):
    
    obs = Observable.create("earth:Region")
    grid = GeometryBuilder().grid(urn=area_WKT, resolution=obs_res).years(obs_year).build()

    ticketHandler = klab.submit(obs, grid)
    context = await ticketHandler.get()

    ticketHandler = context.submit(Observable.create(observable))
    observation = await ticketHandler.get()

    if observation.isEmpty():
        LOGGER.error("Observation is empty, possibly Engine unable to resolve the Semantic Query, no data to export.")
    
    else:

        observation.exportToFile(Export.DATA, export_format, export_path)
        dataflow = context.getDataflow(ExportFormat.KDL_CODE)

        LOGGER.info("Dataflow of the k.LAB Engine Resolution:")
        LOGGER.info(dataflow)

        provenance = context.getProvenance(True, ExportFormat.ELK_GRAPH_JSON)
        LOGGER.info("Following Resources were used in Resolution of the Semantic Query from the Provenance:")

        if context.getResources():
            for resource in context.getResources():
                LOGGER.info(f" Resource ID (URN in k.LAB Semantic Web): {resource.id}")
                LOGGER.info(f" Resource Description: {md(resource.description)}")
                LOGGER.info(f" Resource Authors: {', '.join(resource.authors)}")
        else:
            LOGGER.warning("Unable to fetch resource information from k.LAB Engine")


        if provenance_export_path:
            export_to_html(provenance, provenance_export_path)


def get_klab_instance(fpath: str = None) -> Klab:
    if not fpath:
        try:
            print("Trying Local Engine connection since a credentials file wasn't supplied ")
            klab = Klab.create()
        except:
            raise RuntimeError('Could not establish connection to Remote k.lab engine')
        
    else:
        try:
            print('Trying Remote Engine connection as provided ')
            klab = Klab.create(credentialsFile=fpath)
        except:
            try:
                print('Try Local Engine connection since an attempt was made to connect to the Remote Server and it failed')
                klab = Klab.create()
            except:
                raise RuntimeError('Could not establish connection to a k.lab engine')

    if klab and klab.isOnline():
        print(f'* connection to {klab.engine.url} was successfully established. session: {klab.engine.session_id}')
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


def export_to_html(provenance, output_path: str):
    if isinstance(provenance, str):
        data_obj = json.loads(provenance)
    else:
        data_obj = provenance

    data_js = json.dumps(data_obj)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Dataflow Viewer</title>
  <style>
    body {{ margin: 0; overflow: hidden; font-family: Arial, sans-serif; }}
    svg {{ width: 100vw; height: 100vh; background: #f5f5f5; cursor: grab; }}
    .node {{ fill: #e3f2fd; stroke: #1e88e5; stroke-width: 1.5; }}
    .container {{ fill: #ffffff; stroke: #9e9e9e; stroke-dasharray: 4 3; stroke-width: 1.2; }}
    .edge {{ fill: none; stroke: #333; stroke-width: 1.2; }}
    .label {{ font-size: 12px; pointer-events: none; user-select: none; fill: #111; }}
  </style>
</head>
<body>
<svg id="canvas"></svg>

<script>
const data = {data_js};
const svg = document.getElementById("canvas");

let viewBox = [0, 0, data.width || 800, data.height || 600];
svg.setAttribute("viewBox", viewBox.join(" "));

function setViewBox() {{
  svg.setAttribute("viewBox", viewBox.join(" "));
}}

function clientToSvg(clientX, clientY) {{
  const r = svg.getBoundingClientRect();
  return {{
    x: viewBox[0] + (clientX - r.left) * viewBox[2] / r.width,
    y: viewBox[1] + (clientY - r.top) * viewBox[3] / r.height
  }};
}}

svg.addEventListener("wheel", (e) => {{
  e.preventDefault();
  const zoom = e.deltaY > 0 ? 1.1 : 0.9;
  const mouse = clientToSvg(e.clientX, e.clientY);

  viewBox[0] = mouse.x - (mouse.x - viewBox[0]) * zoom;
  viewBox[1] = mouse.y - (mouse.y - viewBox[1]) * zoom;
  viewBox[2] *= zoom;
  viewBox[3] *= zoom;

  setViewBox();
}});

let isPanning = false;
let start = {{ x: 0, y: 0 }};

svg.addEventListener("mousedown", (e) => {{
  isPanning = true;
  start = {{ x: e.clientX, y: e.clientY }};
  svg.style.cursor = "grabbing";
}});

window.addEventListener("mousemove", (e) => {{
  if (!isPanning) return;
  const r = svg.getBoundingClientRect();
  const dx = (e.clientX - start.x) * viewBox[2] / r.width;
  const dy = (e.clientY - start.y) * viewBox[3] / r.height;

  viewBox[0] -= dx;
  viewBox[1] -= dy;
  setViewBox();

  start = {{ x: e.clientX, y: e.clientY }};
}});

window.addEventListener("mouseup", () => {{
  isPanning = false;
  svg.style.cursor = "grab";
}});

function collectNodes(node, nodes) {{
  if (node && typeof node === "object") {{
    if (node.x !== undefined && node.y !== undefined && node.width !== undefined && node.height !== undefined) {{
      nodes.push(node);
    }}
    (node.children || []).forEach(child => collectNodes(child, nodes));
  }}
}}

function collectEdges(node, edges) {{
  if (node && typeof node === "object") {{
    (node.edges || []).forEach(edge => edges.push(edge));
    (node.children || []).forEach(child => collectEdges(child, edges));
  }}
}}

function edgePath(edge) {{
  const paths = [];
  (edge.sections || []).forEach(sec => {{
    const pts = [sec.startPoint, ...(sec.bendPoints || []), sec.endPoint];
    if (pts.length > 0) {{
      let d = `M ${{pts[0].x}} ${{pts[0].y}}`;
      for (let i = 1; i < pts.length; i++) {{
        d += ` L ${{pts[i].x}} ${{pts[i].y}}`;
      }}
      paths.push(d);
    }}
  }});
  return paths.join(" ");
}}

const nodes = [];
const edges = [];
collectNodes(data, nodes);
collectEdges(data, edges);

edges.forEach(edge => {{
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("class", "edge");
  path.setAttribute("d", edgePath(edge));
  svg.appendChild(path);
}});

nodes.forEach(n => {{
  const x = n.x || 0;
  const y = n.y || 0;
  const w = n.width || 100;
  const h = n.height || 40;
  const label = (n.labels && n.labels[0] && n.labels[0].text) || n.id || "";

  const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
  g.setAttribute("transform", `translate(${{x}},${{y}})`);

  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  rect.setAttribute("class", n.children && n.children.length ? "container" : "node");
  rect.setAttribute("x", "0");
  rect.setAttribute("y", "0");
  rect.setAttribute("width", w);
  rect.setAttribute("height", h);
  rect.setAttribute("rx", "6");
  rect.setAttribute("ry", "6");
  g.appendChild(rect);

  const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
  text.setAttribute("class", "label");
  text.setAttribute("x", w / 2);
  text.setAttribute("y", h / 2);
  text.setAttribute("text-anchor", "middle");
  text.setAttribute("dominant-baseline", "middle");
  text.textContent = label;
  g.appendChild(text);

  svg.appendChild(g);
}});
</script>
</body>
</html>
"""

    Path(output_path).write_text(html_content, encoding="utf-8")