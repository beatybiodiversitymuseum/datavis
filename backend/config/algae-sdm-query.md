# Algae SDM occurrence query review

Specify saved query `707` is the reviewed source for the `algae-sdm-occurrences`
public dataset. The supplied export had 105,427 rows and these 15 displayed
fields: Latitude, Longitude, Locality, Kingdom - Full Name, Division - Full
Name, Class - Full Name, Order - Full Name, Family - Full Name, Genus - Full
Name, Species - Full Name, Continent - Full Name, Country - Full Name, State -
Full Name, County - Full Name, and Sensitive Record. The collection manager
confirmed that a blank Sensitive Record value means the record is approved for
public display. The supplied export had blank values in that field throughout.
The backend rejects refreshes if a future row has a nonblank value in this
field; the last successful cached export remains available.

The climate example uses only latitude, longitude, genus, species, and state.
The API publishes the full reviewed query result; review any future changes to
the saved query's displayed fields and results before retaining its enabled
status.
