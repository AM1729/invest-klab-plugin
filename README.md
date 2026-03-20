# invest-klab-plugin

### Overview
A plugin developed to interact with the [k.LAB Semantic Web](https://klab.integratedmodelling.org/) from the [<b>`InVEST NatCap Project`</b>](https://naturalcapitalalliance.stanford.edu/software/invest). The InVEST Project recently introduced <i>Plugins</i> to help modellers independently build and run their own models that adapt or provide extensions to existing InVEST models, without any gatekeeping. An introduction to InVEST Plugins can be found [here](https://naturalcapitalalliance.stanford.edu/news/new-feature-opens-door-custom-models-mapping-and-valuing-natures-benefits), and the InVEST Plugin Developer Guide is [here](https://invest.readthedocs.io/en/latest/plugins.html).

Users of the InVEST NatCap Project can now integrate their Modelling Pipelines with the k.LAB Semantic Web of Geospatial Data by importing this plugin by going to the <i> Manage Plugins </i> Option after opening the InVEST Workbench and using the following URL: https://github.com/integratedmodelling/invest-klab-plugin.git.

### Uses
This plugin can enable InVEST users access to the ARIES/k.LAB semantic web of data and models, enabling the user to directly retrieve datasets or model outputs relevant to InVEST. Possible applications include: 
- Retrieving input data for an InVEST model, using a semantic reasoning approach designed to select the most approprate fit-for-purpose data for a user's application and spatiotemporal context (i.e., area of interest). A basic understanding of semantic reasoning is a useful prerequisite for understanding how k.LAB selects scientific knowledge and returns it to the user. **add link**. k.LAB is also capable of integrating multiple datasets - for example, global and local datasets, where local data have only partial coverage of a user's spatiotemporal context.
- Since k.LAB can access not just data but _models_, k.LAB offers a means for model intercomparison and validation. For example, a user could compare outputs of a previously run InVEST model with results of other, comparable models or possible validation data sources available in k.LAB's federated network of scientific data and models. This could provide information used to improve the InVEST models or draw additional insights from model intercomparison.
- k.LAB can ultimately act as an intermediary _semantic orchestration_ platform for users to create and execute pipelines integrating models related to ecosystem services - such as biodiversity, ecosystem extent and condition, or nature risk. For example, ARIES offers connections to the [ESA OpenEO platform](https://github.com/integratedmodelling/OpenEO-UDP-UDF-catalogue) to access remotely sensed data and code, and approaches to [modeling ecosystem extent](https://esa-worldecosystems.org/en).
   
Work is also underway to enable InVEST Python code to be directly called using k.LAB model code, supporting bidirectional interoperability between ARIES/k.LAB and InVEST. Doing so will require InVEST [model code to be atomized](https://doi.org/10.1093/gigascience/giae122) and the inputs and outputs of each piece of atomic InVEST code to be semantically annotated, as described below.

### Specifications
For each use, the k.LAB-InVEST Plugin user is required to specify:
- Workspace: The directory which InVEST will use to run the operations
- Path to your [k.LAB Certificate](https://klab.integratedmodelling.org/get-started/), after the user has registered for k.LAB (your user defines groups to which you belong, giving access to different data and models). <br>
Or, alternatively path to the `.properties` file (By default: `$HOME/.klab/credentials.properties`) that contains your Username, Password and the URL of the Engine you wish to connect to.
The Properties file should look like:
```
username=<your username>
password=<your password>
engine=<link to the remote engine>
```
The `engine` points to the k.LAB Engine one wishes to connect to, by default, it should point to the local engine running in the `http://127.0.0.1:8283`. <br>
If a remote engine url is supplied, like: `https://developers.integratedmodelling.org/modeler`, we first try to connect to that, and if it fails, then the fallback is to try to connect to the local engine.

- Spatial Context: A path to a vector `.shp` file can be provided. The supplied geometry is reprojected to EPSG:4326 (WGS84 coordinate reference system, CRS) if not already in that CRS, and a corresponding [WKT string](https://mapscaping.com/a-guide-to-wkt-in-gis/) is generated, e.g.,`POLYGON((33.796 -7.086, 35.946 -7.086, 35.946 -9.41, 33.796 -9.41, 33.796 -7.086))`. This triggers the observation of the specified semantic concept by k.LAB.

- Year: For temporally dynamic data, the relevant year for your analysis. Example - entering 2018 will return data for the year 2018, if annual data are available for that year. If data availability is irregular (e.g., data in 5-year intervals from 2000-2020), k.LAB will return the closest match to the requested year - e.g., 2020 data would be returned rather than data for 2000, 2005, 2010, or 2015.

- Semantic Query: This describes the scientific observable that k.LAB will search for from its federated data and model resources. k.LAB _resolves_ your query by identifying the most appropriate dataset(s) and model(s) for your spatiotemporal request, executes any needed modeling workflow, and returns results. Example - `geography:Elevation` or `distance to infrastructure:Highway`. For further information on syntax and semantics of kim (a DSL based on xtext to develop k.LAB Models) please refer to [k.LAB's technical documentation](https://confluence.integratedmodelling.org/spaces/KIM/pages/20054136/0.2+The+k.IM+language+and+semantic+modelling) (accessible once logged in using your k.LAB user ID and password). It is critical that your semantic query exactly matches the annotation of relevant data and models, in order for the resolution process to work correctly. Since the number of inputs and outputs of InVEST models is relatively limited, it should be possible to develop a shared list of semantic annotations for these inputs and outputs, particularly for the most frequently used InVEST models (see below for examples, based on the InVEST seasonal water yield model). Please post questions [here](https://confluence.integratedmodelling.org/questions), including help requests on semantic annotations for specific InVEST model input/output data.

The Semantic Query is resolved by the k.LAB Engine (Remote or Local), and the result becomes available as `result.tif` in your user-selected Workspace. 

This Plugin is built on the k.LAB Python Client: https://github.com/integratedmodelling/klab-client-python, which is open-source, using the AGPL-3.0 license.

### Example semantic queries for the InVEST Seasonal Water Yield Model

This section maps InVEST model inputs and outputs to ARIES/k.LAB semantics, for the [InVEST Seasonal Water Yield model](
https://storage.googleapis.com/releases.naturalcapitalproject.org/invest-userguide/latest/en/seasonal_water_yield.html), based on an existing [reimplementation of this model in ARIES](https://bitbucket.org/integratedmodelling/im.aries.global/src/a66d8bdffab6c37432b20ee9f4166ed5b8a72cbf/src/aries/global/water/yield.kim?at=master#yield.kim-2
). It thus provides examples of both k.LAB’s semantics underlying semantic principles, and the types of concepts to use in the “Semantic query” portion of the InVEST-k.LAB plugin to query data and models in the federated k.LAB ecosystem. Mapping of concepts representing the inputs and outputs of other InVEST models to ARIES/k.LAB semantics can be similarly completed on an as-needed basis.

For a more complete description of k.LAB’s semantics, see here. In brief, k.LAB’s semantics are designed to be: (1) readily readable by both humans and machines, (2) atomic – i.e., using a smaller, parsimonious and logically consistent set of concepts to build descriptions of more complex scientific observables – rather than using a sprawling vocabulary with a unique concept for every scientific term, which can lead to rapidly loss of critical logical consistency, (3) multidisciplinary, yet discipline-agnostic (i.e., defining each scientific observable in general terms, not always using discipline-specific jargon), and (4) combining a core or upper-level ontology to describe basic scientific concepts with community-endorsed domain (i.e., discipline-specific) terminology when available and when appropriately generalizable. Semantic concepts in k.LAB are typically represented using compact uniform resource identifiers, or [CURIEs](https://cthoyt.com/2021/09/14/curies.html). The examples below also illustrate how different semantics are used to describe different scientifically observable concepts representing measurable quantities (represented using units), unitless numeric indices (e.g., CurveNumber), binary data (e.g., “presence of”), and categorical data (e.g., land cover types, hydrologic soils groups, or climate zones).

Finally, note that calibration parameters are typically not assigned semantics, because these numbers are generally neither physically measurable or modeled quantities nor meaningful beyond the context of a specific model. They are thus not assigned unique semantics, but can be numerically represented in the models as non-semantic numeric values.

| InVEST Seasonal Water Yield model concept   | ARIES/k.LAB semantics      | Notes      |
| ------------- | ------------- | ------------- |
| Actual evapotranspiration | hydrology:Evapotranspiration | “Actual” is unneeded; by convention any measurement actually observed is “actual”       |
| Baseflow | hydrology:BaseFlowWaterVolume in mm/day | Using “mm/day” for this and other concepts enables data to be temporally re-aggregated as appropriate to the model, increasing the data or model’s flexibility |
| Climate zone | ecology.incubation:KoppenGeigerClimateZone |               |
| Crop coefficient (Kc) | hydrology.incubation:CropCoefficient | “incubation” here and elsewhere indicates provisional semantics that may be subject to later revision  |
| Curve number | hydrology:CurveNumber |               |
| Elevation | geography:Elevation in m |               |
| Hydrologic soil group | hydrology:HydrologicSoilGroup |               |
| Land cover | landcover:LandCoverType |               |
| Local recharge | hydrology:InfiltratedWaterVolume in mm/day |               |
| Number of rainfall events per month | count of earth:Storm during im:Month |               |
| Potential evapotranspiration | im:Potential hydrology:EvapotranspiredWaterVolume in mm/day |               |
| Precipitation | earth:PrecipitationVolume in mm/day |               |
| Quickflow | hydrology:RunoffWaterVolume in mm/day |               |
| Stream network | presence of earth:Stream |               |
| Watershed | hydrology:Watershed |               |
