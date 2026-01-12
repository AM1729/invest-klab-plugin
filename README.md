# invest-klab-plugin
A plugin developed to interact with the k.LAB Semantic Web from the InVEST Natcap Project. The InVEST Project recently introduced Plugins to help modellers, build and run their own models allowing improvisations over the existing ones, without any gatekeeping. Further information on Plugins could be found here: https://naturalcapitalalliance.stanford.edu/news/new-feature-opens-door-custom-models-mapping-and-valuing-natures-benefits and the Developer Guide on the same here: https://invest.readthedocs.io/en/latest/plugins.html

Users of the InVEST Natcap Project can now integrate their Modelling Pipelines with the k.LAB Semantic Web of Geospatial Data import this plugin going to the <i> Manage Plugins </i> Option, using the following URL: https://github.com/integratedmodelling/invest-klab-plugin.git

The Plugin requires one to specify :
- Workspace - this refers to a directory which InVEST will use to run the operations
- Path to k.LAB Certificate and this should point to the k.LAB Engine one wishes to connect to - by default it should point to the local engine running in the http://127.0.0.1:8283, 
- Spatial Context in WKT format, WGS84: Example - POLYGON((33.796 -7.086, 35.946 -7.086, 35.946 -9.41, 33.796 -9.41, 33.796 -7.086))
- Year: Example - 2020
- Semantic Query: Example - `geography:Elevation` or `distance to infrastructure:Highway`. For further information on syntax and semantics of kim (a DSL based on xtext to develop k.LAB Models) please refer to the official technical documentation of klab.

The Semantic Query would be Resolved by the k.LAB Engine (Remote or Local), and the result would be available in `result.tif` in the Workspace. 

This plugin builds over the Klab Python Client here: https://github.com/integratedmodelling/klab-client-python


