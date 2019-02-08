title: GIS data and digital maps for hiking in the mountains of Lapland in Northern Sweden (Kungsleden, Sarek and Padjelanta National Parks)
type: article
slug: gis-data-and-digital-maps-for-hiking-in-lapland
tags: [geo, gdal, hiking, kungsleden, sarek]
status: published
date: 2019-02-08

If you've ever done (or plan on doing) any hiking in the Arctic mountains of beautiful Lapland in Northern Sweden, you'll be familiar with the wonderful purple-colored Fjallkartan maps published by Lantmateriet. The hardcopy maps are essential when you're up there, but lately I've found myself wanting to have a digital version of these maps (and other data) as well. 

I have visited the area several times now and feel that digital maps would be helpful in planning trips, mapping tracks after getting back, as an extra layer in a GPS receiver, or even just for experimenting with in QGIS.

So, let's have a look at obtaining some digital copies of the Fjallkartan maps for Northern Sweden, and perhaps an elevation model and some satellite imagery would be nice too. I've included most of the steps and GDAL commands I've used, so if you're interested you should be able to reproduce these types of maps for other areas as well.

You can also skip down to the <a href="#downloads">downloads</a> section at the end if you're only interested in the data.

# Area of interest

The area I'm interested in is the mountain range in Northern Sweden, bordering Norway and surrounding the <a href="https://en.wikipedia.org/wiki/Kungsleden">Kungsleden Trail</a>, from Abisko in the North to the town of Hemavan in the South. The area includes several national parks (Abisko, Sarek, Padjelanta, Stora Sjofallets, Pieljekaise), trails (Kungsleden, Padjelanta) and peaks (Kebnekaise). The area is (depending on your definition) one of Europe's last remaining wildernesses, and the landscapes are absolutely stunning:

![Lapland river crossing](./sweden_0.jpg)

![Lapland panorama](./sweden_1.jpg)

![Lapland glacier](./sweden_2.jpg)

The photos were made by Anthony Arnold during our <a href="https://www.youtube.com/watch?v=_KiSp3mJEDk">hike from Nikkaluokta to Narvik</a> in the summer of 2016.

# Fjallkartan data

I was unable to find ready-made GeoTIFF versions of the maps on the Lantmateriet website (bit of a language barrier, not sure if they're available at all actually) but their <a href="https://kso.etjanster.lantmateriet.se/oppnadata.html">open data site</a> lets you download sections of these maps as PNG images. While these seem like small extracts at first, you can download large sections at once by zooming out your browser with `CTRL-MINUS`, while keeping the map at the detail level that you want. With some cropping and copy-pasting I ended up with a huge image of around 7400 by 10000 pixels (236km by 320km) covering the entire region in sufficient detail:

![Sample image of the topo map](./sample_topo.jpg)

A `gdal_translate` command can be used to convert the RGB bands of the PNG image into an optimized (compressed, tiled, etc) GeoTIFF file. The following command was used to create the final output map `kungsleden_topo.tif`, about 23Mb in size:

    :::console
    gdal_translate \
        -of GTiff \
        -b 1 -b 2 -b 3 \
        -a_srs EPSG:3006 \
        -a_ullr 458832 7610640 695952 7290640 \
        -co COMPRESS=JPEG \
        -co JPEG_QUALITY=90 \
        -co PHOTOMETRIC=YCBCR \
        -co TILED=YES \
        kungsleden_topo.png \
        kungsleden_topo.tif

<center><a href="https://s3.eu-central-1.amazonaws.com/kungsleden-hiking-maps-and-data/kungsleden_topo.tif">Download full topo image as GeoTIFF (23.5Mb)</a></center>

The map is in the `SWEREF99TM` spatial reference system, applied to the image using the `-a_srs EPSG:3006` option. I obtained the extents for the `-a_ullr` option manually by carefully looking up the coordinates of the edges of my original map image. The other creation options defined by `-co` are for optimization purposes. 

# Digital elevation model

The elevation data was obtained from the <a href="https://land.copernicus.eu/imagery-in-situ/eu-dem/eu-dem-v1.1/view">EU-DEM v1.1</a>. I'd like to mostly plot some elevation profiles of routes, so hopefully the EU-DEM is sufficiently detailed for that.

I needed the `E40N50` and `E40N40` tiles to cover the same extent as the Fjallkartan map above. Because I'd like all the datasets to have the same resolution and grid as the first one, we'll use GDAL again to merge and warp both tiles into the same coordinate system and extent as the above map. You have to download and extract the necessary tiles, and merge them together into a temporary VRT file with `gdalbuildvrt`:

    ::console
    gdalbuildvrt \
        temp.vrt \
        eu_dem_v11_E40N40/eu_dem_v11_E40N40.TIF \
        eu_dem_v11_E40N50/eu_dem_v11_E40N50.TIF

And then warp the VRT file into the desired output coordinate system and extent:

    ::console
    gdalwarp \
        -of GTiff \
        -ot Int16 \
        -overwrite \
        -t_srs EPSG:3006 \
        -te 458830 7290650 696048 7610650 \
        -ts 7400 10000 \
        -dstnodata -32768 \
        -co COMPRESS=DEFLATE \
        -co PREDICTOR=2 \
        -co ZLEVEL=1 \
        temp.vrt \
        kungsleden_dem.tif

Setting nodata values, compression, and a conversion from `Float32` to `Int16` data type are also included in the command. Our DEM is now looking good and matches the topo map created earlier:

![Sample image of the elevation model](./sample_dem.jpg)

<center><a href="https://s3.eu-central-1.amazonaws.com/kungsleden-hiking-maps-and-data/kungsleden_dem.tif">Download full DEM image as GeoTIFF (44.9Mb)</a></center>

# Satellite imagery

For the satellite imagery we will use the <a href="https://s2maps.eu/">Sentinel-2 cloudless</a> dataset produced by <a href="https://eox.at/">EOX</a> [1]. There's a few quick wins here: the data is available in GeoTIFF format straight from Amazon S3, it has global coverage, and the different tiling levels let you choose the resolution most suitable to your use case. 

There are various access methods, but I prefer direct access to the tiles via the `eox-s2maps` bucket on Amazon S3. This is a 'Requester Pays' bucket, meaning that you have to set up your AWS account and pay for the data you transfer out of the bucket. I used a <a href="https://github.com/kokoalberti/geocmd/blob/master/s2c-download/s2c-download.py">small script</a> to download 612 tiles at zoom level 11, looking a bit like this for our area of interest:

![Selecting the tiles from the Sentinel cloudless dataset](./cloudless_tiles_sample.jpg)

So now we have 612 tiles of 512 by 512 pixels each in a `tiles` subdirectory. They look a bit squashed and distorted because the area is so far North, but we'll warp them to the same map projection and extent as all our other maps of the region. Again in a two-step approach, first building a mosaic of all the tiles with `gdalbuildvrt`:

    ::console
    gdalbuildvrt \
        temp.vrt \
        tiles/*.tif

And then reprojecting everything with `gdalwarp` to our desired dimensions:

    ::console
    gdalwarp \
        -of GTiff \
        -overwrite \
        -t_srs EPSG:3006 \
        -te 458830 7290650 696048 7610650 \
        -ts 7400 10000 \
        -co COMPRESS=JPEG \
        -co JPEG_QUALITY=90 \
        -co TILED=YES \
        -wo INIT_DEST=255 \
        temp.vrt \
        kungsleden_sat.tif

This results in a nice satellite composite that matches up with our other datasets:

![Sample image of the satellite view](./sample_sat.jpg)

<center><a href="https://s3.eu-central-1.amazonaws.com/kungsleden-hiking-maps-and-data/kungsleden_sat.tif">Download full satellite image as GeoTIFF (24.4Mb)</a></center>

One issue that I encounted was that some of the glaciers are misrepresented as nodata in the tiles, perhaps due to their similarity to clouds, resulting in nodata pixels becoming black on the glaciers. This didn't look so good and was circumvented by setting `-wo INIT_DEST=255`, which initializes the new raster with values of 255, making all nodata pixels white instead.

I have also created a high resolution version (left) of the satellite map using (a lot more) source tiles at zoom level 13, which shows a bit more features than the low-res version (right):

![High-resolution vs low resolution version of the satellite image](./hires_lowres.jpg)

<center><a href="https://s3.eu-central-1.amazonaws.com/kungsleden-hiking-maps-and-data/kungsleden_sat_hires.tif">Download full high resolution satellite image as GeoTIFF (192.3Mb)</a></center>

# Creating maps for a Garmin GPS receiver

I have a Garmin eTrex 30x GPS receiver which supports loading adding an additional map layer called a 'custom map'. Unfortunately you can't just upload your geoferenced GeoTIFF to the device (that would be so straightforward it would just be silly... /s) so there are a couple of extra steps to it.

The gist of it is that a KML file needs to be created with one or more JPEG image overlays in it that contain your map image. The overlays can't be bigger than 1024x1024 pixels each without losing quality, and a maximum of 100 of these overlays are allowed for each map [4]. The images should be in an unprojected geographic coordinate system (`EPSG:4326`) as well.

There are a few programs out there that will do this conversion for you, but I had some mixed results. Maps would get distorted or the quality wouldn't be optimal, and sometimes the georeferencing was even off. I decided to roll my own using some QGIS, GDAL and Python magic. It's not super complicated and after trying it you'll know exactly how it works, which is also good.

## Planning the tiles

First step was to lay out the square tiles I was going to use over the unprojected `EPSG:4326` topo map of the area. This was done in QGIS by using the "Vector Grid" utility, and tweaking the grid size and extent so that (after deleting some unused tiles) there would be less than 100 tiles remaining, in this case 81:

![Sample image of the elevation model](./garmin_tiles.jpg)

QGIS has even been so kind to add `xmin`, `xmax`, `ymin`, and `ymax` coordinates as attributes of each tile. Save the grid as a CSV file with the name `grid.csv`, we'll need it in the next step for cutting out the tiles.

## Creating the tile images and KMZ

Creating the individual tile images turned into a bit of a rabbit hole of GDAL commands, so in the end I decided it would be easier to make small Python script to automate the task and it would be re-usable in the future. The script is called <a href="https://github.com/kokoalberti/geocmd/blob/master/make-garmin-kmz/make-garmin-kmz.py">`make-garmin-kmz.py`</a> and it does the following:

* Read the extent of each of the tiles from a supplied CSV grid file.
* Check if it can parse the `xmin`, `xmax`, `ymin`, and `ymax` columns and that the resulting tile is actually a square.
* For each tile, create a new in-memory `EPSG:4326` raster of 1024 by 1024 pixels, and use <a href="https://gdal.org/python/osgeo.gdal-module.html#Warp">`gdal.Warp()`</a> to warp a part of the original `kungsleden_topo.tif` (or other) map into it.
* Use <a href="https://gdal.org/python/osgeo.gdal-module.html#Translate">`gdal.Translate()`</a> to save the in-memory datasets as JPEG straight into a `custom-map.kmz` file using the GDAL <a href="https://www.gdal.org/gdal_virtual_file_systems.html#gdal_virtual_file_systems_vsizip">`/vsizip/`</a> virtual file system.
* Create a KML file `doc.kml` that contains the index of all the tiles, and add that in the `custom-map.kmz` file.

Run it as:

    ::console
    $ head -5 grid.csv
    id,xmin,xmax,ymin,ymax
    1,16.13210,16.53210,68.13318,68.53318
    2,16.53210,16.93210,68.13318,68.53318
    3,16.93210,17.33210,68.13318,68.53318
    4,17.33210,17.73210,68.13318,68.53318
    $ python3 make-garmin-kmz.py --grid grid.csv --raster kungsleden_sat_hires.tif
    Creating 81 tiles inside custom-map.kmz...
    Done!
    $

I've tuned down the JPEG quality a bit on the final maps to make them load a bit faster on the GPS device as well.

## Loading on the device

Last step is easy, just hook up the Garmin device and copy the KMZ to the `CustomMaps` directory. Restart it, enable the custom maps overlay in the map settings, and the maps should load if you zoom in a little. You can download the Garmin KMZ of the <a href="https://s3.eu-central-1.amazonaws.com/kungsleden-hiking-maps-and-data/garmin_kungsleden_topo.kmz">Topo Overlay (12.0Mb)</a> and the <a href="https://s3.eu-central-1.amazonaws.com/kungsleden-hiking-maps-and-data/garmin_kungsleden_sat.kmz">Satellite Overlay (7.6Mb)</a>.

![Topo map (left) and satellite map (right)](./garmin_custom_maps.jpg)

<center><small>Topo custom map (left) and satellite view (right) on Garmin eTrex 30x receiver</small></center>

<h1 id="downloads">Downloads</h1>

I've hosted all the files on Amazon S3, so feel free to download them from there for your own planning and adventure purposes:

- <a href="https://s3.eu-central-1.amazonaws.com/kungsleden-hiking-maps-and-data/kungsleden_topo.tif">Kungsleden Topo Fjallkartan</a> (23.5Mb, GTiff)
- <a href="https://s3.eu-central-1.amazonaws.com/kungsleden-hiking-maps-and-data/kungsleden_dem.tif">Kungsleden Digital Elevation Model</a> (44.9Mb, GTiff)
- <a href="https://s3.eu-central-1.amazonaws.com/kungsleden-hiking-maps-and-data/kungsleden_sat.tif">Kungsleden Satellite</a> (24.4Mb, GTiff)
- <a href="https://s3.eu-central-1.amazonaws.com/kungsleden-hiking-maps-and-data/kungsleden_sat_hires.tif">Kungsleden Satellite High Res</a> (192.3Mb, GTiff)

The equivalent overlays for your Garmin device:

- <a href="https://s3.eu-central-1.amazonaws.com/kungsleden-hiking-maps-and-data/garmin_kungsleden_topo.kmz">Kungsleden Topo Fjallkartan (Garmin Overlay)</a> (12.0Mb, KMZ)
- <a href="https://s3.eu-central-1.amazonaws.com/kungsleden-hiking-maps-and-data/garmin_kungsleden_sat.kmz">Kungsleden Satellite (Garmin Overlay)</a> (7.6Mb, KMZ)

# Licensing

Please we aware of the licensing requirements of the data sources if you intend to use them. The <a href="https://s2maps.eu">Sentinel 2 cloudless</a> data by <a href="https://eox.at">EOX</a> is licensed under a <a href="https://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>, the Swedish Fjallkartan maps by Lantmateriet are in the public domain and available under a <a href="https://creativecommons.org/share-your-work/public-domain/cc0/">CC-0 License</a>, and see <a href="https://land.copernicus.eu/imagery-in-situ/eu-dem/eu-dem-v1.1?tab=metadata">this page</a> for licensing information for the EU-DEM 1.1 dataset.

# Acknowledgements

Thanks to EOX for creating the wonderful Sentinel-2 cloudless dataset and Landmateriet for their excellent mountain maps of Sweden.

<div class="notes-and-comments">
<h2 class='notes-and-comments'>Disclaimer</h2>
<p class="notes-and-comments">
While every attempt has been made to make the data as accurate as possible, I can't guarantee that it's actually any good for anything. I hope you find it useful for preparation and making some maps using your favourite GIS programme, and don't forget to check out the data sources yourself to ensure that they're fit for your intended purpose.
</p>
<p class="notes-and-comments">
If you're actually venturing out into these areas, prepare yourself properly: bring official and up-to-date maps, know what you're getting yourself into, and most certainly don't rely on things with batteries and LCD screens to find the way there (or back) for you.
</p>

<h2 class='notes-and-comments'>Notes and comments</h2>
<p class="notes-and-comments">
Thanks for reading! While there is no comment functionality on this website, I do appreciate any feedback, questions, improvements, and other ideas about this article. Feel free to contact me directly via e-mail at <a href="mailto:koko@geofolio.org">koko@geofolio.org</a>.
</p>

<h2 class='notes-and-comments'>References</h2>
<p class="notes-and-comments">
[1] Sentinel-2 cloudless - <a href="https://s2maps.eu">https://s2maps.eu</a> by <a href="https://eox.at/">EOX IT Services GmbH</a> (Contains modified Copernicus Sentinel data 2016 & 2017)
</p>
<p class="notes-and-comments">
[2] European Digital Elevation Model (EU-DEM), version 1.1 is available via <a href="https://land.copernicus.eu/imagery-in-situ/eu-dem/eu-dem-v1.1">https://land.copernicus.eu/imagery-in-situ/eu-dem/eu-dem-v1.1</a>
</p>
<p class="notes-and-comments">
[3] Lantmateriet data available via <a href="https://opendata.lantmateriet.se/">https://opendata.lantmateriet.se/</a> and <a href="https://lantmateriet.se/">https://lantmateriet.se/</a>
</p>
<p class="notes-and-comments">
[4] See <a href="https://forums.gpsfiledepot.com/index.php?topic=2832.0">this topic</a> on gpsfiledepot.com for more info on the Garmin map format, as well as this Garmin support page about <a href="https://support.garmin.com/en-IE/?faq=FtEncUXbaE0xE04yZ7gTq5">custom map limitations</a>.
</p>


</div>
