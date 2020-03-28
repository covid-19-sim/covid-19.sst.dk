# Official COVID-19 data from Sundhedsstyrelsen

This is the unofficial repository for the official COVID-19 data covering Denmark from [Sundhedsstyrelsen](https://www.sst.dk).

## Why
Sundhedsstyrelsen is not willing to publish the COVID-19 data in a machine readable format.

For the public to be able to analyse the situation themselves, this repository is created to provide machine readable data for the COVID-19 virus.

## How

The most recent data is grabbed from https://www.sst.dk/da/corona/tal-og-overvaagning using a quick-and-dirty script.
However...

Some historical data that once was released and later has been removed from the above source has been added manually in certain files.
That includes

* Tested and verified before 16.march 2020

Some data is updated manually from a human reading an image showing the data.
That includes

* Deaths

# Comments on data

## Time shift
The *Tested*, *Confirmed* and *Death count* seems to be registered by number at midnight.
That is numbers of tested, confirmed and deaths occurred during a specific calendar day.
The other numbers are published around 13:00 or 14:00 every day, so that is most likely the correct valid number at noon (12:00) every day.
So there is most likely a time shift in the tested, confirmed and death count by approximately 12 hours.

