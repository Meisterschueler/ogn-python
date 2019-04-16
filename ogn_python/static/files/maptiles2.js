
function CoverageMapType() {
  this.start = '2014-04-14';
  this.end = '2200-01-01';
  this.station = "";
  this.source = "max";
  this.colours = [];
  this.colour = '';
}

var id = 0;
var cache = {};
var cacheUTM = {};

CoverageMapType.prototype.setStation = function(newStation) {
  this.station = newStation;
}

CoverageMapType.prototype.setColourScheme = function(_colour) {
  this.colour = _colour;
  var s = _colour.split( ':' );
    
  var start = tinycolor( s[1] ); start = start.toRgb();
  var end = tinycolor( s[0] ); end = end.toRgb();

  console.log( _colour );
  console.log( "start:" );
  console.log( start );
    
  for (i = 0; i < 25; i++) {
    var alphablend = 1-(i/24);
    var c = { r: start.r * alphablend + (1 - alphablend) * end.r,
      g: start.g * alphablend + (1 - alphablend) * end.g,
      b: start.b * alphablend + (1 - alphablend) * end.b,
      a: start.a * alphablend + (1 - alphablend) * end.a };

    this.colours[i] = tinycolor(c).toRgbString();
  }
}

CoverageMapType.prototype.setDates = function(_start,_end) {
  this.start = _start;
  this.end = _end;
}

CoverageMapType.prototype.setSource = function(_source) {
  this.source = _source;
}

let canvasC = null;
CoverageMapType.prototype.canvasFunctionCoverage = function(
  extent,
  resolution,
  pixelRatio,
  size, //  [canvasWidth, canvasHeight],
  projection
) {
  if (!canvasC) {
    canvasC = document.createElement("canvas");
    canvasC.setAttribute("id", "canvasCoverage");
  }
  var canvasWidth = size[0], canvasHeight = size[1];
  canvasC.setAttribute("width", canvasWidth);
  canvasC.setAttribute("height", canvasHeight);
  var contextC = canvasC.getContext("2d");
  // erase the canvas before re-drawing
  contextC.clearRect(0, 0, canvasWidth, canvasHeight);

  // do nothing if too much out zoom
  var zoom = map.getView().getZoom();
  if ( ( zoom < minZoomLevel && this.source != 'lowres-coverage' ) ||
      ( zoom > maxZoomLevel ) ) {
    return canvasC;
  }
    
  // determine coordinates corners TopLeft and BottomRight

  // Canvas extent (larger) is different than map extent
  // need to compute delta between left-top of map and canvas extent.
  var mapExtent = map.getView().calculateExtent(map.getSize())
  var canvasOrigin = map.getPixelFromCoordinate([extent[0], extent[3]]);
  var mapOrigin = map.getPixelFromCoordinate([mapExtent[0], mapExtent[3]]);
  var delta = [ mapOrigin[0]-canvasOrigin[0], mapOrigin[1]-canvasOrigin[1] ];
//  var mapOpposite = map.getPixelFromCoordinate([mapExtent[2], mapExtent[1]]);

  //convert from pixel to xy
  var xyTL = map.getCoordinateFromPixel([0,0]);
  var xyBR = map.getCoordinateFromPixel([canvasWidth,canvasHeight]);

  // convert from xy to lat/long
  var latlonTL = ol.proj.transform(xyTL, 'EPSG:3857', 'EPSG:4326');
  var latlonBR = ol.proj.transform(xyBR, 'EPSG:3857', 'EPSG:4326');
  
  // plot a square that has been fetched
  // each item is ~1 km square
  function plotRef(json) {
        
    // convert from lat/long to canvas pixels	
    var toScreen = function(latlonPoint) {
      var xyPoint = ol.proj.transform(latlonPoint, 'EPSG:4326', 'EPSG:3857');
	  var pxPoint = map.getPixelFromCoordinate(xyPoint);
	  return ( [ (pxPoint[0]+delta[0])*pixelRatio, (pxPoint[1]+delta[1])*pixelRatio ] );
    }
    
    function fillBox(x) {
      var tl = toScreen([x[0],x[1]]); var br = toScreen([x[2],x[3]]);
      contextC.fillRect( tl[0], tl[1], br[0] - tl[0], br[1] - tl[1] );
    }

    if ( coverageOverlay.colours.length > 0 && json.p ) {
      // expand out the compressed data - smaller over the network
      var points = [];
      json.p.forEach( function(position) {
        var data = position.split('/');
        var mgrs = json.t + data[0];
        points.push( { a: data[1], m: mgrs } );
        if ( ! cacheUTM[ mgrs ] ) {
          cacheUTM[ mgrs ] = inverse( mgrs );
        }
      } );

      contextC.save();
      contextC.globalAlpha = 1;
      contextC.lineWidth = 0.2;
      for( var i = 250, p = 1000000, n = 0; i >= 10; p = i, i-=10, n++ ) {
        contextC.fillStyle = contextC.strokeStyle = coverageOverlay.colours[ n ];
        var t = i/5;
        
        points.forEach( function(position) {
          if ( position.a >= i && position.a < p ) {
            fillBox( cacheUTM[ position.m ] );
          }
        });
      }
      contextC.restore();
    }
	map.render(); // redraw map after every plotref
  };

  var tiles = {}; // 0.1 deg by 0.1 deg (~11 km square)
  for( var x = Math.min(latlonTL[0],latlonBR[0]), xm = Math.max(latlonTL[0],latlonBR[0]); x <= xm ;x+= 0.1 ) {
    for( var y = Math.min(latlonBR[1],latlonTL[1]), ym = Math.max(latlonBR[1],latlonTL[1]); y <= ym; y+= 0.1 ) {
      tiles[ forward([x,y],1).substr(0,5) ] = 1;
    }
  }

  var source = coverageOverlay.source;
  var station = coverageOverlay.station;
  var start = coverageOverlay.start;
  var end = coverageOverlay.end;
  
  // fetch each square
  Object.keys(tiles).sort().forEach( function(tile) {
    var cacheKey =  tile+source+station+start+end;
    if ( ! cache[cacheKey] ) {
      cache[cacheKey] = [ plotRef ];

      $.ajax({   type: "GET",
        url: OgR+"/perl/"+source+"-tile-mgrs.pl",
        data: { station: station, start: start, end: end, squares: tile},
        timeout:20000,
        cache: true,
        error: function (xhr, ajaxOptions, thrownError) {
        },
        success: function(json) { 
          cache[cacheKey].forEach( function(x) { x(json); } ); cache[cacheKey] = undefined; 
        }
      });
    } else {
      cache[cacheKey].push( plotRef );
    }
  });

  $(document).ajaxStop(function () {
      // 0 === $.active
  });
  return canvasC;
}

function bound(value, opt_min, opt_max) {
  if (opt_min != null) value = Math.max(value, opt_min);
  if (opt_max != null) value = Math.min(value, opt_max);
  return value;
}

function AmbiguityMapType() {
  this.ambiguity = false;
}

AmbiguityMapType.prototype.setAmbiguity = function(_ambiguity) { 
  this.ambiguity = _ambiguity;
}

let canvasA = null;
AmbiguityMapType.prototype.canvasFunctionAmbiguity = function(
  extent,
  resolution,
  pixelRatio,
  size,  //  [canvasWidth, canvasHeight],
  projection
) {
  if (!canvasA) {
    canvasA = document.createElement("canvas");
    canvasA.setAttribute("id", "canvasAmbiguity");
  }
  var canvasWidth = size[0], canvasHeight = size[1];
  canvasA.setAttribute("width", canvasWidth);
  canvasA.setAttribute("height", canvasHeight);
  var contextA = canvasA.getContext("2d");
  // erase the canvas before re-drawing
  contextA.clearRect(0, 0, canvasWidth, canvasHeight);

  // do nothing if too much out zoom (<7)
  var zoom = map.getView().getZoom();
  if ( zoom < 7 && this.source != 'lowres-coverage' )  {
    return canvasA;
  }
    
  // determine coordinates corners TopLeft and BottomRight

  // Canvas extent (larger) is different than map extent
  // need to compute delta between left-top of map and canvas extent.
  var mapExtent = map.getView().calculateExtent(map.getSize())
  var canvasOrigin = map.getPixelFromCoordinate([extent[0], extent[3]]);
  var mapOrigin = map.getPixelFromCoordinate([mapExtent[0], mapExtent[3]]);
  var delta = [mapOrigin[0]-canvasOrigin[0], mapOrigin[1]-canvasOrigin[1]]
//  var mapOpposite = map.getPixelFromCoordinate([mapExtent[2], mapExtent[1]]);

  //convert from pixel to xy
  var xyTL = map.getCoordinateFromPixel([0,0]);
  var xyBR = map.getCoordinateFromPixel([canvasWidth,canvasHeight]);

  // convert from xy to lat/long
  var latlonTL = ol.proj.transform(xyTL, 'EPSG:3857', 'EPSG:4326');
  var latlonBR = ol.proj.transform(xyBR, 'EPSG:3857', 'EPSG:4326');
  
// TBD for V4, draw squares in transition zone properly instead of limiting to 45
  // draw ambiguity if selected and if latitude > 45 deg
/*  if ( ambiguity && latlonTL[1] > 45 && latlonBR[1] > 45 )*/ {

    // convert from lat/long to canvas pixels	
    var toScreen = function(latlonPoint) {
      var xyPoint = ol.proj.transform(latlonPoint, 'EPSG:4326', 'EPSG:3857');
	  var pxPoint = map.getPixelFromCoordinate(xyPoint);
	  return ( [ (pxPoint[0]+delta[0])*pixelRatio, (pxPoint[1]+delta[1])*pixelRatio ] );
    }
    
	var shiftBits = 7;
//	var truncBits = 16;  // V4
	var truncBits = 19;  // V5
	var scaleBits = 1e7/(1<<(shiftBits+truncBits));

    // lets draw the lines; horizontal first then vertical
    contextA.save();
    contextA.strokeStyle = 'red';

    for( var t = (latlonBR[1] * scaleBits)|0, 
      r = ((latlonTL[1] * scaleBits)|0)+1; t <= r; t++) {
        
      var s = toScreen( [ latlonTL[0], t / scaleBits ] );
      var f = toScreen( [ latlonBR[0], t / scaleBits ] );
        
      contextA.beginPath();
      contextA.moveTo(s[0],s[1]);
      contextA.lineTo(f[0],f[1]);
      contextA.stroke();
    }
    
//    var shiftBits = (( (latlonTL[1] <= 45) && (latlonTL[1] >= -45) ? 7 : 8) );  // V4
    var shiftBits = 7;  // V5
//	var truncBits = 16;  // V4
	var truncBits = 20;  // V5
	var scaleBits = 1e7/(1<<(shiftBits+truncBits));

    for( var t = (latlonTL[0] * scaleBits)|0, 
      r = ((latlonBR[0] * scaleBits)|0)+1; t <= r; t++) {
        
      var s = toScreen( [ t / scaleBits, latlonTL[1] ] );
      var f = toScreen( [ t / scaleBits, latlonBR[1] ] );
        
      contextA.beginPath();
      contextA.moveTo(s[0],s[1]);
      contextA.lineTo(f[0],f[1]);
      contextA.stroke();
    }
    contextA.restore();
  }
  return canvasA;
}
