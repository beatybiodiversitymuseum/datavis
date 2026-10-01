# Herbarium algae saved-query specification

Specify saved query `685` in collection `Algae` (`collection ID 32768`) uses
Collection Object as the base table. The query must return one row per specimen
and expose these displayed columns in this exact order and with these aliases:

| Alias | Schema Explorer path | Specify label | Purpose |
|---|---|---|---|
| `catalogNumber` | `collectionobject.catalogNumber` | Accession Number | Stable specimen identifier |
| `collectionDate` | `collectionobject.collectingEvent.endDate` | Date Collected | Date and timeline charts |
| `localityName` | `collectionobject.collectingEvent.locality.localityName` | Location | Tables and map hover text |
| `latitude` | `collectionobject.collectingEvent.locality.latitude1` | Latitude | Public map |
| `longitude` | `collectionobject.collectingEvent.locality.longitude1` | Longitude | Public map |
| `country` | `collectionobject.collectingEvent.locality.geography.Country.fullName` | Country → Full Name | Geographic filter |
| `stateProvince` | `collectionobject.collectingEvent.locality.geography.State.fullName` | State → Full Name | Geographic filter |
| `collectorFirstName` | `collectionobject.collectingEvent.collectors.agent.firstName` | First Name | Construct collector display name |
| `collectorMiddleInitial` | `collectionobject.collectingEvent.collectors.agent.middleInitial` | Middle Initial | Construct collector display name |
| `collectorLastName` | `collectionobject.collectingEvent.collectors.agent.lastName` | Last Name | Collector filter and timeline |

Before enabling it:

1. Restrict the query to the Algae collection and exclude any records or fields
   that are not approved for public disclosure.
2. Confirm collector joins do not create duplicate specimen rows. If multiple
   collectors do create rows, agree on a primary-collector query rule rather
   than deduplicating silently in this service.
3. Run the query and compare representative values with `algae.csv` from
   `beatybiodiversitymuseum/Herbarium_Dashboard`.
4. Set its positive saved-query ID in `datasets.yaml` and change `enabled` to
   `true`. The backend will reject a result whose columns differ from the exact
   contract above.
