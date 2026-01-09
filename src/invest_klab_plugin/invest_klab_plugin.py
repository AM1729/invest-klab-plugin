import logging
import os

from natcap.invest import validation
from natcap.invest import utils
from natcap.invest.unit_registry import u
from natcap.invest import gettext
from natcap.invest import spec
from klab.klab import Klab
from shapely import wkt

LOGGER = logging.getLogger(__name__)

MODEL_SPEC = spec.ModelSpec(
    model_id="klab",
    model_title=gettext("klab Plugin"),
    module_name=__name__,
    userguide='https://github.com/AM1729/invest-klab-plugin/blob/main/README.md',
    input_field_order=[
        ['workspace_dir'],
        ['kim_semantic_query'],
        ['spatial_context'],
        ['klab_certificate_path']],

    inputs=[
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

        spec.StringInput(
            id="kim_semantic_query",
            name=gettext("kim semantic query"),
            about=gettext(
                "Semantic Query based on kim, required to query the Klab Semantic Web"
                "of GeoSpatial Data"),
            required=True,
            regexp="[a-zA-Z0-9_-]*"
        ),

        spec.StringInput(
            id='spatial_context',
            name='Spatial Context (WKT)',
            about=gettext(
                'Spatial Context following the WKT Format'),
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
    
    LOGGER.info('Done!')


@validation.invest_validator
def validate(args, limit_to=None):
    if 'spatial_context' in args:
        try:
            wkt.loads(args['spatial_context'])
        except wkt.WKTReadingError:
            raise ValueError('Invalid WKT format for spatial context')
        
    return validation.validate(args, MODEL_SPEC)