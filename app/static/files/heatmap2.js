
var map;
var map_id = 0;
var position;
var lastPosition;
var stations = {};
var station_markers = {};
var labelled_markers = {};
var timeoutId;
var coverageOverlay;
var start = '2018-01-01';
var end = '2100-01-01';
var lasthash = '';
var maxTimeout, minTimeout;
var processingUrl = true;
var defaultPointer = 'crosshair'; // help, cursor, crosshair, text, wait, pointer, progress
//var defaultColor = '#00990000:#009900ff';
var defaultColour = '#80000040:#008000ff';
var minZoomLevel = 8;
var maxZoomLevel = 11;

var selected = { 'what':'max', 'when':'lastweek', 'station':'', 'center':'', 'zoom':'', 'airspace':'', 'airports':'', 'circles':'', 'ambiguity':'', 'colour': defaultColour };

function initialize() {

  airspaceLayer = new ol.layer.Tile({
    source: new ol.source.XYZ({
      tileUrlFunction: function(tileCoord, projection) {
        var z = tileCoord[0];
        var x = tileCoord[1];
        var y = (1 << z) + tileCoord[2];
        return 'http://1.tile.maps.openaip.net/geowebcache/service/tms/1.0.0/openaip_approved_airspaces_geometries@png/' + z + '/' + x + '/' + y + '.png';
      },
      wrapx: false
    }),
    opacity: 1,
    visible: false
  });
    
  airportsLayer = new ol.layer.Tile({
    source: new ol.source.XYZ({
      tileUrlFunction: function(tileCoord, projection) {
        var z = tileCoord[0];
        var x = tileCoord[1];
        var y = (1 << z) + tileCoord[2];
        return 'http://1.tile.maps.openaip.net/geowebcache/service/tms/1.0.0/openaip_approved_airports@png/' + z + '/' + x + '/' + y + '.png';
      },
      wrapx: false
    }),
    opacity: 1,
    visible: false
  });
    
  OSMLayer = new ol.layer.Tile({
    source: new ol.source.OSM(),
    visible: true
  });
        
  stationLayerSource = new ol.source.Vector({
    features: []
  });
    
  stationLayer = new ol.layer.Vector({  
    source: stationLayerSource,
    zIndex: 50,
    opacity: 1,
    visible: true
  });
    
  circleLayerSource = new ol.source.Vector({
    features: []
  });
    
  circleLayer = new ol.layer.Vector({   
    source: circleLayerSource,
    zIndex: 50,
    opacity: 1,
    visible: false
  });
    
  AmbiguitySquareLayerSource = new ol.source.Vector({
    features: []
  });
    
  AmbiguitySquareLayer = new ol.layer.Vector({   
    source: AmbiguitySquareLayerSource,
    zIndex: 51,
    opacity: 1,
    visible: true
  });
    
  ambiguityOverlay = new AmbiguityMapType();

  // ratio: 1.2, +/-10% instead of default +/-25%
  ambiguityLayer = new ol.layer.Image({
    source: new ol.source.ImageCanvas({
      canvasFunction: ambiguityOverlay.canvasFunctionAmbiguity,
      projection: "EPSG:3857",
      ratio: 1.2,
      visible: false
    })
  });

  // create overlay before reading hash
  coverageOverlay = new CoverageMapType();

  // ratio: 1.2, +/-10% instead of default +/-25%
  coverageLayer = new ol.layer.Image({
    source: new ol.source.ImageCanvas({
      canvasFunction: coverageOverlay.canvasFunctionCoverage,
      projection: "EPSG:3857",
      ratio: 1.2
    })
  });

  // read hash before creating map with intial settings
  if ( location.hash.substr(1) != '' ) {
    readhash();
  } else {
    setOptions('circles', 'circles'); // show by default
    setColour( defaultColour );
    processingUrl = false;
  }
  // re-readhash if user changed hash and then redraw
  $(window).bind( 'hashchange', reReadhash );

  attribution = new ol.control.Attribution({
    collapsed: true,
    tipLabel: 'Show credits'
  });
    
  scaleLineControl = new ol.control.ScaleLine();        
      
  map = new ol.Map({
    layers: [
      OSMLayer,
      circleLayer,
      airportsLayer,
      airspaceLayer,
      coverageLayer,
      ambiguityLayer,
      stationLayer,
    ],
    target: 'map_canvas',
    controls: ol.control.defaults({
      attributionOptions: {
        collapsible: true
      }
    }).extend([
      scaleLineControl,
      attribution
    ]),
    view: new ol.View({
      projection: 'EPSG:3857',
      center: ol.proj.fromLonLat([dLon,dLat]),
      zoom: dZoom
    }),
  });

  myresize();

  $(window).resize(function () {
    myresize();
  });

  // displays credits over the list
  credits = document.getElementsByClassName('ol-attribution ol-unselectable ol-control')[0];
  credits.style.zIndex = "1000";
        
  var tooltip = document.getElementById('tooltip');
  var overlay = new ol.Overlay({
    element: tooltip,
    offset: [10, 0],
    positioning: 'bottom-left'
  });
  map.addOverlay(overlay);

  function genericDisplayTooltip(evt) {
    var pixel = evt.pixel;
    var feature = map.forEachFeatureAtPixel(pixel, function(feature) {
      return feature;
    });
    tooltip.style.display = feature ? '' : 'none';
    if (feature) {
      overlay.setPosition(evt.coordinate);
      tooltip.innerHTML = feature.get('info');
    }
  };
  
  // marker tooltip
  function displayTooltip(event) {

    var hit = map.hasFeatureAtPixel(event.pixel);

    var pixel = event.pixel;
    tooltip.style.display = 'none';
    map.getTargetElement().style.cursor = defaultPointer;
    map.forEachFeatureAtPixel(pixel, function(feature) {
      if (typeof(feature.get('mark'))!='undefined'){
        if ( feature.get('mark').substring(0,1) == "S" ) {
          overlay.setPosition(event.coordinate);
          tooltip.innerText = feature.get('info');
          tooltip.style.display = '';
          // also change cursor
          map.getTargetElement().style.cursor = 'pointer';
          return;
        }   
      }  
    })  
  };
  map.on('pointermove', displayTooltip);

  map.on('singleclick', function(event) {
    var stationName = '';
    map.forEachFeatureAtPixel(event.pixel, function(feature,layer) {
      if (typeof(feature.get('mark'))!='undefined'){
        if ( feature.get('mark').substring(0,1) == "S" ) {
          stationName = feature.get('name');
        }
      }
    });
    if (stationName != '') {
      getStationData( stationName );
    } else { // no 'S' feature
      // map click - display details
      updateDetails('<b><font color="red">loading...</font></b>');
      if ( timeoutId ) { 
        clearTimeout(timeoutId);
      }
      position = ol.proj.transform(event.coordinate, 'EPSG:3857', 'EPSG:4326');;
      timeoutId = setTimeout( displayDetails, 500 );
    }
  });
    
  map.on('moveend', function(event) {
    var zoom = map.getView().getZoom();
    if (zoom != dZoom) {
      setZoom(zoom);
      updateURL( 'zoom' );
    }
    var nc = ol.proj.toLonLat( map.getView().getCenter() );
    if ( (dLon != round(nc[0],6)) || (dLat != round(nc[1],6)) ) {
	  setCentre( nc );
      updateURL( 'center' );
    }
  });

  // display the stations
  displayStations( true );

  updateDetails("Blue icons represent UP old stations, Mauve ones DOWN<br/>Green is 0.2.1 or above and UP, Red is DOWN new stations");

  timeoutId = null;
};

  function myresize() {
	var h = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
    var t = $('#top_row').height();
	var b = $('#bottom_row').height();
	$('#map_canvas').height((h - t - b) + 'px');  
    map.updateSize();
  }

function addLabel( location, labelText ) {
  var marker = labelled_markers[location.s] = 
    new ol.Feature({
      geometry: new ol.geom.Point(ol.proj.fromLonLat([location.lg,location.lt])),
      mark: "L"
    });
                
    marker.setStyle(new ol.style.Style({
      text: new ol.style.Text({
        font: '12px Verdana',
        text: labelText,
        offsetX: 0,
        offsetY: -22,
        fill: new ol.style.Fill({color: 'black'}),
        stroke: new ol.style.Stroke({color: 'black', width: 0.5})
      })
    }));
  stationLayerSource.addFeature(marker);
}

// custom marker
var angleMarker = 30;
var radiusMarker = 11;
var sinMarker = Math.sin(degreesToRadians(angleMarker));
var cosMarker = Math.cos(degreesToRadians(angleMarker));
var offsetMarker = radiusMarker/sinMarker;
var styleCache = {};
var styleFunction = function(colour) {
  colour = '#'+colour;
  var style = styleCache[colour];
  if (!style) {
    canvasM = document.createElement("canvas");
    var canvasWidth = radiusMarker*2+3, canvasHeight = radiusMarker+offsetMarker+3;
    canvasM.setAttribute("width", canvasWidth);
    canvasM.setAttribute("height", canvasHeight);
    var contextM = canvasM.getContext("2d");
    // erase the canvas before re-drawing
    contextM.clearRect(0, 0, canvasWidth, canvasHeight);
    // Draw
    contextM.save();
    contextM.beginPath();
    var x1=radiusMarker*cosMarker, y2=radiusMarker+offsetMarker;
	var y1=offsetMarker-radiusMarker*sinMarker, x2=x1*y2/y1;
    contextM.moveTo(radiusMarker+1, canvasHeight-0);
    contextM.lineTo(radiusMarker+1-x1, canvasHeight-y1);
    contextM.arcTo(radiusMarker+1-x2, canvasHeight-y2, radiusMarker+1, canvasHeight-y2, radiusMarker);
    contextM.arcTo(radiusMarker+1+x2, canvasHeight-y2, radiusMarker+1+x1, canvasHeight-y1, radiusMarker);
    contextM.closePath();
    contextM.fillStyle = colour;
    contextM.fill();
    contextM.lineWidth = 1;
    contextM.strokeStyle = '#000000';
    contextM.stroke();
    contextM.restore();

    style = new ol.style.Style({
      image: new ol.style.Icon({
        img: canvasM,
        imgSize: [canvasWidth, canvasHeight],
        anchor: [0.5, 1.0],
      })
    });
    styleCache[colour] = style;
  }
  return style;
};
	  
function addStation( location, colour ) {
  var marker = station_markers[location.s] = 
    new ol.Feature({
      geometry: new ol.geom.Point(ol.proj.fromLonLat([location.lg,location.lt])),
      lat: location.lt,
      lon: location.lg,
      info: location.s + "\n" + (location.u == "U" ? "Last heartbeat at:\n" : "Last point at ") + location.ut + "Z\n"  + "Version " + location.v,
      mark: "S",
      name: location.s,
    });
                
    marker.setStyle(styleFunction(colour)); // custom
/*    marker.setStyle(new ol.style.Style({
      image: new ol.style.Icon({
        anchor: [0.5, 1],
        opacity: 1,
        src: "//www.googlemapsmarkers.com/v1/" + colour + "/",
      })
    })); */
  stationLayerSource.addFeature(marker);
}

function addCircle( location, radius, colour ) {
  var rangeCircle =
    new ol.Feature({
//      geometry: new ol.geom.Circle(ol.proj.fromLonLat([location.lg, location.lt]), radius / Math.cos( degreesToRadians(location.lt)))
        geometry: new ol.geom.Polygon.circular(
        // WGS84 Sphere
        new ol.Sphere(6378137),
        [location.lg, location.lt],
        radius,
        // Number of verticies
        64).transform('EPSG:4326', 'EPSG:3857')
    });

    rangeCircle.setStyle(new ol.style.Style({
      stroke: new ol.style.Stroke({
      color: colour,
      width: 1
    }),
  }));
  circleLayerSource.addFeature(rangeCircle);
}    

var dsTimeOut = null;
function displayStations(first) {
  // Ajax is async and timeout runs twice unless cleared until AJAX done
  // so need a clearTimeOut
  if (dsTimeOut) {
    clearTimeout(dsTimeOut);  
  }

  $.ajax( {   type: "GET",
    url: OgR+"/perl/stations2-filtered.pl?start="+start+"&end="+end,
    timeout:20000,
    cache: true,
    error: function (xhr, ajaxOptions, thrownError) {
    },
    success: function(json) {
      var checked = selected['circles'] == 'circles';

      stationLayerSource.clear()
      station_markers = {};
      stations = [];

      circleLayerSource.clear()

      // add markers
      json.stations.forEach( function(entry) {
        stations[entry.s] = entry;

        var old = (entry.v == 'old' || entry.v == '?' || entry.v == "undefined" || entry.v == "" || entry.v == '0.1.3' );
        var colour = '00ff00';
        if ( entry.u == "U" ) {
          if ( old ) {
            colour = '0000ff';
          }
        } else {
          if ( old ) {
            colour = 'aa00aa';
          } else {
            colour = 'aa0000';
          }
        }
        addStation( entry, colour );

        addCircle( entry, 10000, 'rgba(48, 48, 48, 0.7)' );
        addCircle( entry, 20000, 'rgba(48, 48, 48, 0.5)' );
        addCircle( entry, 30000, 'rgba(48, 48, 48, 0.3)' );
      } );

      if ( first ) {
        setupSearch();
        var stationName = selected['station'];
        stationName = matchStation(stationName);
        if ( stationName != "" && stations[stationName] ) {
		  setStation(stationName); // as per match
          setCentre( [ stations[stationName].lg, stations[stationName].lt ] );
          map.getView().setCenter(ol.proj.fromLonLat([dLon, dLat]));
        }
      }
    }
  });

  // and update every 5 minutes
  dsTimeOut = setTimeout( displayStations, 5*60*1000 );
}

function degreesToRadians(deg) {
  return deg * (Math.PI / 180);
}

function radiansToDegrees(rad) {
  return rad / (Math.PI / 180);
}

function round(value, decimals) {
  return Number(Math.round(value+'e'+decimals)+'e-'+decimals);
}

const DEFAULT_RADIUS = 6371008.8;
function getDistance(c1, c2, opt_radius) {
  const radius = opt_radius || DEFAULT_RADIUS;
  const lat1 = degreesToRadians(c1[1]);
  const lat2 = degreesToRadians(c2[1]);
  const deltaLatBy2 = (lat2 - lat1) / 2;
  const deltaLonBy2 = degreesToRadians(c2[0] - c1[0]) / 2;
  const a = Math.sin(deltaLatBy2) * Math.sin(deltaLatBy2) +
    Math.sin(deltaLonBy2) * Math.sin(deltaLonBy2) *
    Math.cos(lat1) * Math.cos(lat2);
  return 2 * radius * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function clearLabels() {
  // remove old labels
  // use Object.keys for array with keys instead of numeric indexes
  Object.keys(labelled_markers).forEach(function(key, index) {
    stationLayerSource.removeFeature(labelled_markers[key]);
  });
  labelled_markers = [];
}

function getStationData( stationName ) {
  clearLabels();
  updateDetails('');
  adjustMap( null, null, stationName );
};

function updateDetails(newDetails) {
  if (newDetails != '') {
    $('#details').show();
  } else {
    $('#details').hide();
  }
  $('#details').html(newDetails);
  myresize();  // adjust, details DIV may change size
}

function displayDetails() {
  if ( position && position != lastPosition ) {
    $.ajax( {   type: "GET",
      url: OgR+"/perl/details-mgrs.pl",
      data: { start: start, end: end, position: forward([position[0],position[1]],2) },
      timeout:20000,
      cache: true,
      error: function (xhr, ajaxOptions, thrownError) {
      },
      success: function(json) {
        console.log( json.toString() );
        var pos = inverse( json.query.ref );
        var bounds = ol.extent.boundingExtent([[pos[0],pos[1]],[pos[2],pos[3]]])
        var point = ol.extent.getCenter(bounds);
        clearLabels();
        var stationList = "";
        var id = 1;
        var currentFilter = selected['station'];
        json.position.forEach( function(station) {
          var distance = stations[station.s] ? Math.round(
            getDistance([stations[station.s].lg, stations[station.s].lt],point)
              /100)/10 : '?';            
          if ( currentFilter != '' && station.s != currentFilter ) {            
            stationList += "<i class='subtle'>";            
          }            
          stationList += "<b>"+id+":"+station.s+"</b>: "+distance+"km, "+station.l+"-"+station.h+"m, Avg Max:"+(station.a/10)+"db,  Samples:"+station.c + ", Gliders:"+station.g+ ' ('+station.first;            

          if ( station.first != station.last ) {            
            stationList +=  " to " + station.last;            
          }            
          stationList += ')<br/>';            

          if ( currentFilter != '' && station.s != currentFilter ) {            
            stationList += "</i>";            
          }            
          if ( station_markers[station.s] ) {            
            addLabel( stations[station.s], id.toString() );
          }            
          id++;            
        });            
        console.log( stationList );            
        updateDetails(stationList);
      },
    });
    lastPosition = position;
  }
  timeoutId = null;
}

var substringMatcher = function(strs) {
  return function findMatches(q, cb) {
    var matches, substringRegex;

    matches = [];
    substrRegex = new RegExp(q, 'i');
    for( var key in stations ) {
      if (substrRegex.test(key)) {
        matches.push({ value: key });
      }
    } 
    cb(matches.sort(function(a,b){ return a.value < b.value ? -1 : (a.value == b.value ? 0 : 1); }));
    cb(matches);
  };
};

function setupSearch() {
  $('.stationlist #typeahead').typeahead({ 
    hint: true,
    highlight: true,
    minLength: 1
  },
  {
    name: 'stations',
    displayKey: 'value',
    source: substringMatcher('')
  });
}

function toggleOptions(option) {
  var newOption = selected[option] ? '' : option;
  setOptions(option, newOption);
  updateURL(option);
  return false;
}

function setOptions(option, newOption) {
  switch(option) {
    case 'circles':
      circleLayer.setVisible(newOption);
      break;
    case 'ambiguity':
      ambiguityLayer.setVisible(newOption);
      break;
    case 'airports':
      airportsLayer.setVisible(newOption);
      break;
    case 'airspace':
      airspaceLayer.setVisible(newOption);
      break;
    default: {
	}
  }
  tick( option, newOption );
}

function setMinColour(c,a) {
  var s = selected['colour'].split(':');
  if ( s[0] != c ) {
    s[0] = c+pad2(a.toString(16)); 
    adjustMap( null, null, null, s[0]+':'+s[1] );
  } 
  return false;
}

function setMaxColour(c,a) {
  var s = selected['colour'].split(':');
  if ( s[1] != c ) {
    s[1] = c+pad2(a.toString(16)); 
    adjustMap( null, null, null, s[0]+':'+s[1] );
  } 
  return false;
}

function setZoom(mapZoom) {
  console.log( "Zoom level: "+mapZoom );
  dZoom = mapZoom;
  selected['zoom'] = mapZoom;
  if (mapZoom > maxZoomLevel) {
    $('#zoomOut_msg').show();
  }
  else {
    $('#zoomOut_msg').hide();
  }
  if (mapZoom < minZoomLevel) {
    $('#zoomIn_msg').show();
  }
  else {
    $('#zoomIn_msg').hide();
  }
  return false;
}

function setCentre(coords) {
  dLon = coords[0];
  dLat = coords[1];
  selected['center'] = coords[1].toFixed(5) + "_" + coords[0].toFixed(5);
}
	  
function setColour(colour) {
  selected['colour'] = colour;
  coverageOverlay.setColourScheme( colour );
}

function setStation(where) {
  selected['station'] = where;
  coverageOverlay.setStation(where);
  $('#typeahead').val( where );
  updateTitle();
}

function setSource(what) {
  tick( 'what', what );
  coverageOverlay.setSource(what);
  updateTitle();
}
	
function setDates(when) {
  switch(when) {
    case 'today':
      start = end = new Date().toISOString().substr(0,10);
      break;
    case 'yesterday':
      start = new Date(new Date().getTime() - (24*3600*2*1000)).toISOString().substr(0,10);
      end = new Date(new Date().getTime() - (24*3600*1*1000)).toISOString().substr(0,10);
      break;
    case 'lastweek':
      start = new Date(new Date().getTime() - (24*3600*7*1000)).toISOString().substr(0,10);
      end = new Date().toISOString().substr(0,10);
      break;
    case 'recent':
      start = new Date(new Date().getFullYear(),0,1).toISOString().substr(0,10);
      end = new Date().toISOString().substr(0,10);
      break;
    case 'all':
      start = '2015-03-31';
      end = new Date().toISOString().substr(0,10);
      break;
    default: {
      switch(when.substr(0,1)) {
        case 'd':
	      var ndays = parseInt(when.substr(1,10));
          start = new Date(new Date().getTime() - (24*3600*ndays*1000)).toISOString().substr(0,10);
          end = new Date().toISOString().substr(0,10);
          break;
        case 'D':
          var s = when.substr(1,21).split('#');
          start = s[0];
          end = s[1];
          break;
        default: {
		}
      }
    }
  }
  tick( 'when', when );
  coverageOverlay.setDates( start, end );
  updateTitle();
}

function setWhen(when) {
  adjustMap(null, when);
  return false;
}

function setWhat(what) {
  adjustMap(what);
  return false;
}

function matchStation(where) {
  if (where != '') { // match in list
    for( var key in stations ) {
      if (where.toUpperCase() == stations[key].s.toUpperCase()) {
        where = stations[key].s;
        break;
      }
    }
  }
  return where;
}
	  
var nostation = { 'receivers':1, 'coverage':1 };
function adjustMap( what, when, where, colour ) {

  if ( what ) {
    setSource(what);
    if ( nostation[what] ) {
      where = '';
    }
    updateURL(what);
  }
  if ( when ) {
	setDates(when);
    updateURL(when);
  }
  if ( where != null && where != undefined ) {
    if (where == '') {  // i.e all stations
      setStation(where);    
      updateURL('station');
	} else {
      if (where.includes('%')) {  // i.e contains wildcard
        setStation(where);    
        updateURL('station');
	  } else {
        where = matchStation(where);
        var LngLat;
        if ( stations[ where ] ) {
          LngLat = [stations[where].lg,stations[where].lt];
          if (map.getView().getZoom() < minZoomLevel ) {
            setZoom(minZoomLevel);
	        map.getView().setZoom(dZoom);
          }	
	      setCentre( LngLat );
          map.getView().setCenter(ol.proj.fromLonLat([dLon, dLat]));

          setStation(where);
          updateURL('station');
        } else {
          $('#typeahead').val('');
        }
	  }
	}
  }
  if ( colour != null && colour != '' ) {
    setColour(colour);
    updateURL('colour');
  }
  // update the coverage layer
  coverageLayer.getSource().changed();
}

var hrefOrder = [ 'station', 'what', 'when', 'center', 'zoom', 'colour' ]; 
var updateHistory = { 'what':1, 'when':1, 'station':1 };
var titleOrder = [ 'what', 'station', 'when' ];
var options = [ 'airports', 'airspace', 'circles', 'ambiguity' ]; 

function tick( whattype, newItem ) {
  // clear current tick
  if ( selected[whattype] && selected[whattype] !== '' && whattype !== 'station' )  {
    $('#'+selected[whattype]+' span').attr('class','');
  }
  selected[whattype] = newItem;
  // set new tick
  if ( selected[whattype] && selected[whattype] !== '' && whattype !== 'station' )  {
    $('#'+selected[whattype]+' span').attr('class','glyphicon glyphicon-ok');
  }
}
    
function updateTitle() {
  // update the title to reflect the contents
  var title = '';
  for( var i = 0; i < titleOrder.length; i++ ) {
    var v = selected[titleOrder[i]];
    if ( v && v != '' ) {
      if ( titleOrder[i] == 'station' ) {
        title += ' - ' + v;
      } else {
        title += ' - ' + $('#'+v).text();
      }
    }
  }
  window.document.title = 'Onglide Range' + title;
  $('#description').html( title.substr(2) );
}

var coloursInitialised = false;
function initColour( newColour ) {

  var s = newColour.split(':');

  var startColor = tinycolor( s[1] ); 
  var endColor = tinycolor( s[0] ); 

  if (coloursInitialised) { // update
    $("#maxc").trigger("colorpickersliders.updateColor", startColor.toRgbString());
    $("#minc").trigger("colorpickersliders.updateColor", endColor.toRgbString());
    return;
  }

  $("#maxc").ColorPickerSliders({
    color: startColor.toRgbString(),
    flat: true,
    size: 'sm',
    placement: 'left',
    customswitches: false,
    order: {
      hsl: 1,
      opacity: 2
    },
    onchange: function( container, colour ) {
      if ( maxTimeout ) { clearTimeout( maxTimeout ); }
      maxTimeout = setTimeout( function() { 
        setMaxColour( colour.tiny.toHexString(), Math.round(colour.rgba.a*255) );
      }, 500 );
    }
  }); 

  $("#minc").ColorPickerSliders({
    color: endColor.toRgbString(),
    flat: true,
    size: 'sm',
    placement: 'left',
    customswitches: false,
    order: {
      hsl: 1,
      opacity: 2
    },
    onchange: function( container, colour ) {
      if ( minTimeout ) { clearTimeout( minTimeout ); }
      minTimeout = setTimeout( function() { 
        setMinColour( colour.tiny.toHexString(), Math.round(colour.rgba.a*255) );
      }, 500 );
    }
  });
  coloursInitialised = true;
}

function updateURL( whattype )  {
  // and if we aren't processing a URL hash at the moment then
  //  update the URL as well
  if ( ! processingUrl ) {
    var url = '#';
    for( var i = 0; i < hrefOrder.length; i++, url += ',' ) {
      if ( selected[hrefOrder[i]] ) {
        url += selected[hrefOrder[i]];
      }
    }

    for( i = 0; i < options.length; i++ ) {
      if ( selected[options[i]] ) {
        url += options[i] + ";";
      }
    }

    // we changed it, this will stop us doing anything with it
    lasthash = url;
//    if ( history.pushState && updateHistory[whattype] ) { 
//      history.pushState( null, null, url );
//    } else {
      location.replace( url );
//    }
  }
}

function reReadhash() {
  // make sure the hash isn't the same as we think it is
  //  this should stop us parsing our own changes
  if ( location.hash === lasthash ) {
    return;
  }
  readhash();
  // update map
  map.getView().setZoom(dZoom);
  map.getView().setCenter(ol.proj.fromLonLat([dLon, dLat]));
  // make sure canvas redrawn if zoom and center stays same !!!
  // update the coverage layer
  coverageLayer.getSource().changed();
}

function readhash() {
  lasthash = location.hash;
  processingUrl = true;
  var vals = location.hash.substr(1).split(',');
  console.log( location.hash.substr(1) + "|%%%%|" + vals[0] );

  // do options first as adjustMap will force the redraw
  if ( vals[6] ) {
    var userOptions = vals[6].split(';');
    var newOption = ~(userOptions.indexOf('airports')) ? 'airports' : '';
	setOptions('airports', newOption);
    newOption = ~(userOptions.indexOf('airspace')) ? 'airspace' : '';
	setOptions('airspace', newOption);
    newOption = ~(userOptions.indexOf('circles')) ? 'circles' : '';
	setOptions('circles', newOption);
    newOption = ~(userOptions.indexOf('ambiguity')) ? 'ambiguity' : '';
	setOptions('ambiguity', newOption);
  }

  // set colour
  if ( vals[5] ) { 
    setColour( vals[5] );
  } else {
    setColour( defaultColour );
  }
  initColour(selected['colour']);

  // set date
  if (vals[2]) { 
    setDates(vals[2]);
  } else {
    setDates('all');
  }

  // set graph source
  if ( vals[1] ) { 
    setSource(vals[1]);
  }
  
  // set station
  if ( vals[0] ) { 
    setStation(vals[0]);
  }

  // set center (lat_lon)
  if ( vals[3] ) {
    var coords = vals[3].split('_');
    if ( coords.length ) {
	  setCentre( [ parseFloat(coords[1]), parseFloat(coords[0]) ] );
    }
  }

  // set zoom
  if ( vals[4] ) {
    setZoom(parseInt(vals[4]));
  }
  processingUrl = false;
}
    
// Force a hex value to have 2 characters
function pad2(c) {
  return c.length == 1 ? '0' + c : '' + c;
}
