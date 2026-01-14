# invest-klab-plugin
A plugin developed to interact with the [k.LAB Semantic Web](https://klab.integratedmodelling.org/) from the [<b>`InVEST NatCap Project`</b>](https://naturalcapitalalliance.stanford.edu/software/invest). The InVEST Project recently introduced <i>Plugins</i> to help modellers independently build and run their own models that adapt or provide extensions to existing InVEST models, without any gatekeeping. An introduction to InVEST Plugins can be found [here](https://naturalcapitalalliance.stanford.edu/news/new-feature-opens-door-custom-models-mapping-and-valuing-natures-benefits), and the InVEST Plugin Developer Guide is [here](https://invest.readthedocs.io/en/latest/plugins.html).

Users of the InVEST NatCap Project can now integrate their Modelling Pipelines with the k.LAB Semantic Web of Geospatial Data by importing this plugin by going to the <i> Manage Plugins </i> Option after opening the InVEST Workbench and using the following URL: https://github.com/integratedmodelling/invest-klab-plugin.git.

For each use, the k.LAB-InVEST Plugin user is required to specify:
- Workspace - the directory which InVEST will use to run the operations
- Path to [k.LAB Certificate](https://klab.integratedmodelling.org/get-started/), pointing to the k.LAB Engine one wishes to connect to. By default, it should point to the local engine running in the `http://127.0.0.1:8283`, 
- Spatial Context in WKT format, WGS84: Example - `POLYGON((33.796 -7.086, 35.946 -7.086, 35.946 -9.41, 33.796 -9.41, 33.796 -7.086))`
- Year: Example - 2020
- Semantic Query: Example - `geography:Elevation` or `distance to infrastructure:Highway`. For further information on syntax and semantics of kim (a DSL based on xtext to develop k.LAB Models) please refer to the official technical documentation of k.LAB.

The Semantic Query is resolved by the k.LAB Engine (Remote or Local), and the result becomes available in `result.tif` in the Workspace. 

This Plugin is built on the k.LAB Python Client: https://github.com/integratedmodelling/klab-client-python, which is open-source, using the AGPL-3.0 license.


