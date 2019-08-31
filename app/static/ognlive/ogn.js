/*
   ____                      _____ _ _     _             _   _      _                      _    
  / __ \                    / ____| (_)   | |           | \ | |    | |                    | |   
 | |  | |_ __   ___ _ __   | |  __| |_  __| | ___ _ __  |  \| | ___| |___      _____  _ __| | __
 | |  | | '_ \ / _ \ '_ \  | | |_ | | |/ _` |/ _ \ '__| | . ` |/ _ \ __\ \ /\ / / _ \| '__| |/ /
 | |__| | |_) |  __/ | | | | |__| | | | (_| |  __/ |    | |\  |  __/ |_ \ V  V / (_) | |  |   < 
  \____/| .__/ \___|_| |_|  \_____|_|_|\__,_|\___|_|    |_| \_|\___|\__| \_/\_/ \___/|_|  |_|\_\
        | |                                                                                     
        |_|                                                                                     
*/


var map;
var map_id = 0;
var autoc = "";
var acaff = "";
var cton = false;
//var tcolor = ["000000", "FF0000", "00FF00", "0000FF", "FFFF00", "00FFFF", "FF00FF", "C0C0C0", "FFFFFF"];
var tcolor = ["000000","FF0000","00B000","0000FF","808000","008080","FF00FF","606060","505028","500000","800080","FF8040","80B000","4040FF","804000","000080"];
var ccolor = 0;
var aflist = true;
var vallpolon = true;
var vallpoloff = true;
var vallmaron = true;
var vallmaroff = true;
var lside = 0; // 0=right 1=left
var online = []; //         ([cn,alt*1,cn+"_"+ps,colcn,afdif]);
var offline = []; //         ([cn,alt*1,cn+"_"+ps,colcn,afdif]);
var receivers = [];
var all = 0;
var stick = 0;
var barogram = 0;
var pathl = 30; // path length 5' (30points)
var polwidth = 2; // polyline width (path)
var lastpol;		// last polyline name display in divInfo
var unit = "m"; // metric units
var onoff = 1; // 1: online, 2: offline, 3: Menu
var onoffaff = "OnLine";
var triasc = 1; // 1: asc 2: desc
var tricol = 0; // 0:tri sur cn 1: tri sur alti
var ett1 = "<CENTER><IMG style=\"z-index:50\" onclick=\"alist();\" SRC=\"" + tld + "/pict/min.png\">&nbsp;&nbsp;<IMG style=\"z-index:50\" onclick=\"sideclick();\" SRC=\"" + tld + "/pict/dbarrow.gif\">&nbsp;&nbsp;<A HREF=\"" + tld + "/help-fr.html\" target=\"_blank\"><IMG style=\"z-index:50\" SRC=\"" + tld + "/pict/hel.png\"></A>&nbsp;&nbsp;<span id=\"onoff\" onclick=\"onofff();\"></span></CENTER>";
var w = 0; // watchdog variable
var tmgm, tmwd;
var nbreq = 0; // nb request launch
var wlt = 0; // tasks white list
var wlist = [];
var vasp = false;
var vrec = false;
var vrecl = false;
var vstm = false;
var vapt = false;
var vwin = false;
var vpre = false;
var vtem = false;
var vrai = false;
var hnew = false;
selrec = "";
var ftype = ["unknown", "Glider/MotorGlider", "Tow Plane", "Helicopter", "Parachute", "Drop Plane", "Hangglider", "Paraglider", "Plane", "Jet", "UFO", "Balloon", "Airship", "Drone", "unknown", "Static Object"];
var ftypec = ["_b", "", "_g", "_r", "_b", "_b", "_p", "_p", "_b", "_b", "_b", "_b", "_b", "_k", "_b", "_b"];
var initialResolution = 2 * Math.PI * 6378137 / 256; // == 156543.0339
var originShift = 2 * Math.PI * 6378137 / 2.0; // == 20037508.34
var m2ft={"m":1, "i":3.2808};
var am2ft={"m":"m", "i":"ft"};
var kh2kt={"m":1, "i":0.53996};
var akh2kt={"m":"km/h", "i":"kt"};
var m2kt={"m":1, "i":1.94384};
var am2kt={"m":"m/s", "i":"kt"};
var unitlist = {"m":"metric", "i":"nautical"}


var hashc="",hashz="",hashm="",hasho="",hashb="",hashs="",hashl="",hasht="",hl="       ",hashw="",hashu="",hashp="",hashn="",hashy="",hasha="",    hashg="";
// center     zoom    maptype  offline  bound   autoset2ma  layers  tasks                warning   units   pathlength nolist devtype altitudestick barogram 


//  close popup
function cp() {
  clearTimeout(tmop);
  var d = document.getElementById('popup');
  d.style.display = 'none';
}

//  open popup
function op(maxw) {
  var d = document.getElementById('popup');
  d.style.display = 'block';
  d.style.width = maxw + 'px';
  d.style.height = maxw + 'px';
  tmop = setTimeout(cp, 15000);
}

function chunit() { // change units
  if (document.getElementById('uni').checked === true) { // units imperial
    unit = 'i';
    hashu = "&u=i";
  } else { // units metric
    unit = 'm';
    hashu = "";
  }
	scaleLineControl.setUnits(unitlist[unit]);
  rehash();
}

function chstick() { // change altitude stick
  if (document.getElementById('stick').checked === true) { // stick visible
    stick = 1;
    hasha = "&a=1";
		sticksLayer.setVisible(true);
  } else { // no altitude stick
    stick = 0;
    hasha = "";
		sticksLayer.setVisible(false);
  }
  rehash();
}

function chbaro() { // change barogram
  if (document.getElementById('baro').checked === true) { // barogram visible
    document.getElementById('dbaro').style.display = "block";
		document.getElementById('dbaro').style.visibility = "visible";
    barogram = 1;
    hashg = "&g=1";
  } else { // no barogram
    document.getElementById('dbaro').style.display = "none";
    barogram = 0;
    hashg = "";
  }
  rehash();
}

function chpl() { // change path length
  var prevPathl = pathl;
  if (document.getElementById('rp1').checked === true) { // 5 minutes
    pathl = 30;
    hashp = "";
  } else if (document.getElementById('rp2').checked === true) { // 10 minutes
    pathl = 60;
    hashp = "&p=2";
  } else { // all points
    pathl = 99999;
    hashp = "&p=3";
  }
  // only delete paths if new path is smaller
  if (pathl < prevPathl) { 
    delpon();
    delpoff();
  }
  baro_reSize();
	
  rehash();
}

function chmap(mid) {		// change map
	OSMLayer.setVisible(false);
	MapsForFreeLayer.setVisible(false);
	MapsForFreeLayerW.setVisible(false);
	OSMTopoLayer.setVisible(false);
	IGNSatelliteLayer.setVisible(false);
	switch(mid)
    {
      case 1:
				OSMTopoLayer.setVisible(true);
        break;
			case 2:
				MapsForFreeLayer.setVisible(true);
				MapsForFreeLayerW.setVisible(true);
        break;
			case 3:
				IGNSatelliteLayer.setVisible(true);
				break;
			default:
				mid = 0;
        OSMLayer.setVisible(true);
    }
  hashm = "&m=" + mid;
	rehash();
}


function devtype() { // devices types selected
  var dt = 0;
  if (document.getElementById('ICAObox').checked) {
    dt += 1;
  }
  if (document.getElementById('Flarmbox').checked) {
    dt += 2;
  }
  if (document.getElementById('OGNbox').checked) {
    dt += 4;
  }
  if (dt == 7) hashy = ""; // all devices
  else hashy = "&y=" + dt;
  reseton();
  resetoff();
  rehash();
}


function onofff() {
  switch (onoff) {
    case 1:
      if (all == 1) {
        onoffaff = "OffLine";
        onoff = 2;
      } else {
        onoffaff = "Menu";
        onoff = 3;
        document.getElementById("ett2").style.display = "none";
        document.getElementById("dtlist").style.display = "none";
        document.getElementById("menu").style.display = "block";
      }
      break;
    case 2:
      onoffaff = "Menu";
      onoff = 3;
      document.getElementById("ett2").style.display = "none";
      document.getElementById("dtlist").style.display = "none";
      document.getElementById("menu").style.display = "block";
      break;
    case 3:
      onoffaff = "OnLine";
      onoff = 1;
      document.getElementById("ett2").style.display = "block";
      document.getElementById("dtlist").style.display = "block";
      document.getElementById("menu").style.display = "none";
      break;
  }
  afftab();
}

function delpon() { // delete all online path
  var j = -1;
  while (online[++j]) {
    // * window["P_" + online[j][2]].getPath().clear();
		window["P_" + online[j][2]].getGeometry().setCoordinates([]);
    window["M_" + online[j][2]].set('tra', 0);
    window["B_" + online[j][2]] =[];
  }
}

function delpoff() { // delete all offline path
  var j = -1;
  while (offline[++j]) {
    // * window["P_" + offline[j][2]].getPath().clear();
		window["P_" + offline[j][2]].getGeometry().setCoordinates([]);
    window["M_" + offline[j][2]].set('tra', 0);
    window["B_" + offline[j][2]] =[];
  }
}

function deletepath(pol) {
  // * window[pol].getPath().clear();
	window[pol].getGeometry().setCoordinates([]);
	
  window["M_" + pol.substring(2)].set('tra', 0);
  window["B_" + pol.substring(2)] =[];
}

function deleteallpath() {
  if (onoff == 1) {
    delpon();
  } else {
    delpoff();
  }
}


function allpath() {
  var j = -1;
  if (onoff == 1) {
    if (vallpolon === true) vallpolon = false;
    else vallpolon = true;
    while (online[++j]) {
		setvisipol(vallpolon, "P_" + online[j][2]);
    }
  } else {
    if (vallpoloff === true) vallpoloff = false;
    else vallpoloff = true;
    while (offline[++j]) {
		setvisipol(vallpoloff, "P_" + offline[j][2]);
    }
  }
  afftab();
}

function allmarker() {
  var j = -1;
	var opa = true;
  if (onoff == 1) {
    if (vallmaron === true) { 
			vallmaron = false;
			opa = false;
		}
    else vallmaron = true;
    while (online[++j]) {
			setvisimar(opa, "M_" + online[j][2]);
			setvisipol(opa, "S_" + online[j][2]);
    }
  } else {
    if (vallmaroff === true) {
			vallmaroff = false;
			opa = false;
		}
    else vallmaroff = true;
    while (offline[++j]) {
			setvisimar(opa, "M_" + offline[j][2]);
			setvisipol(opa, "S_" + offline[j][2]);
    }
  }
	//map.render();
  afftab();
}




function tricn() {
  if (tricol == 1) triasc = 1;
  else if (triasc == 1) triasc = 2;
  else triasc = 1;
  tricol = 0;
  afftab();
}

function trialti() {
  if (tricol === 0) triasc = 1;
  else if (triasc == 1) triasc = 2;
  else triasc = 1;
  tricol = 1;
  afftab();
}

function focuson(poly) {
  if (document.getElementById(poly) !== null) document.getElementById(poly).className = 'yel';
	/* ###
  window[poly].setOptions({
    strokeWeight: 4,
    strokeOpacity: 1
  });
	*/
}

function focusoff(poly) {
  if (document.getElementById(poly) !== null) document.getElementById(poly).className = 'whi';
	/* ###
  window[poly].setOptions({
    strokeWeight: 2,
    strokeOpacity: 0.75
  });
	*/
}

function asp() {
  if (document.getElementById('aspbox').checked) {
    vasp = true;
		airspaceoverlay.setVisible(true);
    rempl(4, "z");
  } else {
    vasp = false;
		airspaceoverlay.setVisible(false);
    rempl(4, " ");
  }
  rehash();
}

function apt() {
  if (document.getElementById('aptbox').checked) {
    vapt = true;
		airportoverlay.setVisible(true);
    rempl(5, "a");
  } else {
    vapt = false;
		airportoverlay.setVisible(false);		
    rempl(5, " ");
  }
  rehash();
}

function wind() {
  if (document.getElementById('winbox').checked) {
    vwin = true;
		windoverlay.setVisible(true);
		if (map.getView().getZoom() > 7 ) map.getView().setZoom(7);
    rempl(2, "v");
  } else {
    vwin = false;
		windoverlay.setVisible(false);
    rempl(2, " ");
  }
  rehash();
}

function pres() {
  if (document.getElementById('prebox').checked) {
    vpre = true;
		presoverlay.setVisible(true);
		if (map.getView().getZoom() > 7 ) map.getView().setZoom(7);
    rempl(3, "p");
  } else {
    vpre = false;
		presoverlay.setVisible(false);
    rempl(3, " ");
  }
  rehash();
}

function tempe() {
  if (document.getElementById('tembox').checked) {
    vtem = true;
		tempoverlay.setVisible(true);
		if (map.getView().getZoom() > 7 ) map.getView().setZoom(7);
    rempl(1, "t");
  } else {
    vtem = false;
		tempoverlay.setVisible(false);
    rempl(1, " ");
  }
  rehash();
}

function rain() {
  if (document.getElementById('raibox').checked) {
    vrai = true;
		rainoverlay.setVisible(true);
		if (map.getView().getZoom() > 7 ) map.getView().setZoom(7);
    rempl(7, "n");
  } else {
    vrai = false;
		rainoverlay.setVisible(false);
    rempl(7, " ");
  }
  rehash();
}

function hidenew() {
  if (document.getElementById('hnewbox').checked) hnew = true;
  else hnew = false;
}

function reseton() { // delete all online markers and their path
  var j = -1;
  while (online[++j]) {
		iconLayerSource.removeFeature(window["M_" + online[j][2]]);
    delete window["M_" + online[j][2]];
		
		sticksLayerSource.removeFeature(window["S_" + online[j][2]]);
    delete window["S_" + online[j][2]];
		
		traceLayerSource.removeFeature(window["P_" + online[j][2]]);
    delete window["P_" + online[j][2]];
		
    delete window["B_" + online[j][2]];
  }
map.render();	
}

function resetoff() { // delete all offline markers and their path
  var j = -1;
  while (offline[++j]) {
		iconLayerSource.removeFeature(window["M_" + offline[j][2]]);
    delete window["M_" + offline[j][2]];
		
		sticksLayerSource.removeFeature(window["S_" + offline[j][2]]);
    delete window["S_" + offline[j][2]];
		
		traceLayerSource.removeFeature(window["P_" + offline[j][2]]);
    delete window["P_" + offline[j][2]];
		
    delete window["B_" + offline[j][2]];
  }
map.render();
}


function lineoff() {
  if (document.getElementById('offl').checked) {
    all = 0;
    resetoff();
    hasho = "";
  } else {
    all = 1;
    hasho = "&o=1";
  }
  rehash();
}

function bounds() {
  if (document.getElementById('boundsbox').checked) {
    bound = true;
    if (document.getElementById('astmbox').checked) {
      vstm = false;
      hashs = "";
      document.getElementById('astmbox').checked = false;
    }
    amax = parseFloat(document.getElementById('latmax').value);
    amin = parseFloat(document.getElementById('latmin').value);
    if (amin > amax) {
      var tmp = amax;
      amax = amin;
      amin = tmp;
    }
    omax = parseFloat(document.getElementById('lonmax').value);
    omin = parseFloat(document.getElementById('lonmin').value);
    if (omin > omax) {
      var tmp = omax;
      omax = omin;
      omin = tmp;
    }
    if (amax > 85) amax = 85;
    if (amin < -85) amin = -85;
    if (omax > 180) omax = 180;
    if (omin < -180) omin = -180;
    boundc = "&b=" + amax + "&c=" + amin + "&d=" + omax + "&e=" + omin;
    document.getElementById('latmax').value = amax;
    document.getElementById('latmin').value = amin;
    document.getElementById('lonmax').value = omax;
    document.getElementById('lonmin').value = omin;
    reseton();
    resetoff();
    hashb = "&b=" + amax.toFixed(4) + "," + amin.toFixed(4) + "," + omax.toFixed(4) + "," + omin.toFixed(4);
  } else {
    bound = false;
    if (vstm === false) boundc = "";
    hashb = "";
  }
  rehash();
}

function afftab() {
  var j = -1;
  var dlistd = "<TABLE class=\"tt\">";
  var mar = "";
  var pol = "";
  var affcpt = "";

  switch (onoff) {
    case 1:
      online.sort(ASC);
      if (triasc == 2) online.reverse();
      while (online[++j]) {
        mar = "M_" + online[j][2];
        pol = "P_" + online[j][2];
        stk = "S_" + online[j][2];

			  dlistd += "<TR id=\"" + pol + "\" onmouseover=\"focuson('" + pol + "');\" onmouseout=\"focusoff('" + pol + "');\">" + 
		  "<TD class=\"cgv\"><input onchange=\"setvisimar(this.checked ,'" + mar + "');setvisistk(this.checked ,'" + stk + "');\" type=\"checkbox\" " + isvisib(mar) + " ></TD>" + 
		  "<TD class=\"cgv\"><input onchange=\"setvisipol(this.checked ,'" + pol + "');\" type=\"checkbox\" " + isvisib(pol) + " ></TD>" + 
		  "<TD class=\"cgn\" onmousedown=\"centeron('" + mar + "');\" onmouseup=\"centeroff();\" oncontextmenu=\"event.stopPropagation(); redraw('" + pol + "'); return false;\" ondblclick=\"event.stopPropagation(); autocenter('" + mar + "');\" >" + online[j][0] + "</TD>" + 
		  "<TD class=\"cgc\"><span style='background-color: " + online[j][3] + "' ondblclick=\"deletepath('" + pol + "'); return false;\" oncontextmenu=\"this.style.backgroundColor=changecolor('" + mar + "'); return false;\">&nbsp;&nbsp;</span></TD>" + 
		  "<TD onclick=\"affinfo('" + mar + "')\" class=\"cga\">";
      
        if (unit == "i") {
          dlistd += (online[j][1] * m2ft[unit]).toFixed();
        } // { var tv=online[j][1]*m2ft[unit];   dlistd+= tv.toFixed(); }
        else dlistd += online[j][1] + "m";
        dlistd += "</TD><TD class=\"cgv\"><IMG src='" + tld + "/pict/" + online[j][4] + ".gif'></TD></TR>";
      }
      affcpt = " (" + online.length + ")";
      break;
    case 2:
      offline.sort(ASC);
      if (triasc == 2) offline.reverse();
      while (offline[++j]) {
        mar = "M_" + offline[j][2];
        pol = "P_" + offline[j][2];
        stk = "S_" + offline[j][2];
        dlistd += "<TR id=\"" + pol + "\" onmouseover=\"focuson('" + pol + "');\" onmouseout=\"focusoff('" + pol + "');\"><TD class=\"cgv\"><input onchange=\"setvisimar(this.checked ,'" + mar + "');setvisistk(this.checked ,'" + stk + "');\" type=\"checkbox\" " + isvisib(mar) + " ></TD><TD class=\"cgv\"><input onchange=\"setvisipol(this.checked ,'" + pol + "');\" type=\"checkbox\" " + isvisib(pol) + " ></TD><TD class=\"cgn\" onmousedown=\"centeron('" + mar + "');\" onmouseup=\"centeroff();\" oncontextmenu=\"event.stopPropagation(); redraw('" + pol + "'); return false;\" ondblclick=\"event.stopPropagation(); autocenter('" + mar + "');\" >" + offline[j][0] + "</TD><TD class=\"cgc\"><span style='background-color: " + offline[j][3] + "' ondblclick=\"deletepath('" + pol + "'); return false;\" oncontextmenu=\"this.style.backgroundColor=changecolor('" + mar + "'); return false;\">&nbsp;&nbsp;</span></TD><TD onclick=\"affinfo('" + mar + "')\" class=\"cga\">";
//        dlistd += "<TR id=\"" + pol + "\" onmouseover=\"focuson('" + pol + "');\" onmouseout=\"focusoff('" + pol + "');\"><TD class=\"cgv\"><input onchange=\"vpolmar(this.checked ,'" + mar + "');\" type=\"checkbox\" " + isvisib(mar) + " ></TD><TD class=\"cgv\"><input onchange=\"vpolmar(this.checked ,'" + pol + "');\" type=\"checkbox\" " + isvisib(pol) + " ></TD><TD class=\"cgn\" onmousedown=\"centeron('" + mar + "');\" onmouseup=\"centeroff();\" oncontextmenu=\"event.stopPropagation(); redraw('" + pol + "'); return false;\" ondblclick=\"event.stopPropagation(); autocenter('" + mar + "');\" >" + offline[j][0] + "</TD><TD class=\"cgc\"><span style='background-color: " + offline[j][3] + "' ondblclick=\"deletepath('" + pol + "'); return false;\" oncontextmenu=\"this.style.backgroundColor=changecolor('" + mar + "'); return false;\">&nbsp;&nbsp;</span></TD><TD onclick=\"affinfo('" + mar + "')\" class=\"cga\">";
        if (unit == "i") {
          dlistd += (offline[j][1] * m2ft[unit]).toFixed();
        } else dlistd += offline[j][1] + "m";
        dlistd += "</TD><TD class=\"cgv\"><IMG src='" + tld + "/pict/" + offline[j][4] + ".gif'></TD></TR>";
      }
      affcpt = " (" + offline.length + ")";
      break;
    case 3:
      affcpt = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
      break;
  }
  dlistd += "</TABLE>";
  document.getElementById("dtlist").innerHTML = dlistd;
  if (aflist === true) document.getElementById("onoff").innerHTML = "<B>" + onoffaff + "</B>" + affcpt;

}

function ASC(a, b) {
  a = a[tricol];
  b = b[tricol];
  if (a > b)
    return 1;
  if (a < b)
    return -1;
  return 0;
}


function alist() {
  if (aflist === true) {
    document.getElementById("ett1").innerHTML = "<CENTER><IMG style=\"z-index:50\" onclick=\"alist();\" SRC=\"" + tld + "/pict/plu.png\"></CENTER>";
    document.getElementById('dlist').style.width = "20px";
    document.getElementById('dlist').style.height = "20px";
    if (lside == 1) document.getElementById('ac').style.left = "0px";
    else document.getElementById('ac').style.right = "0px";
    centeroff();
    document.getElementById('dbaro').style.display = "none";
    aflist = false;
    hashn = "&n=0";
  } else {
    document.getElementById("ett1").innerHTML = ett1;
    document.getElementById('dlist').style.width = "180px";
    document.getElementById('dlist').style.height = "90%";
    if (lside == 1) document.getElementById('ac').style.left = "180px";
    else document.getElementById('ac').style.right = "180px";
    if (document.getElementById('baro').checked) document.getElementById('dbaro').style.display = "block";
    aflist = true;
    afftab();
    hashn = "";
  }
  rehash();
}

function sideclick() {			// change list position (left<->right) 
  if (lside === 0) {
    document.getElementById('dlist').className = "lleft";
    document.getElementById('dbaro').className = "baroright";
    document.getElementById('ac').className = "acleft";
    document.getElementById('ac').style.right = "";
    lside = 1;

  } else {
    document.getElementById('dlist').className = "lright";
    document.getElementById('dbaro').className = "baroleft";
    document.getElementById('ac').className = "acright";
    document.getElementById('ac').style.left = "";
    lside = 0;

  }
}


function autocenter(mark) {
  // ### document.getElementById("divInfoac").innerHTML = "<B>AC</B>: " + window[mark].get('title');
  autoc = mark;
  // ### document.getElementById("divInfoac").style.display = "block";
	map.getView().setCenter(ol.proj.fromLonLat([window[mark].get('lon'), window[mark].get('lat')]));
}



function centeron(mark) {
  cton = true;
	map.getView().setCenter(ol.proj.fromLonLat([window[mark].get('lon'), window[mark].get('lat')]));
}


function centeroff() {
  if (autoc !== "") {
		map.getView().setCenter(ol.proj.fromLonLat([window[autoc].get('lon'), window[autoc].get('lat')], 'EPSG:4326', 'EPSG:3857'));
  }
  cton = false;
}


function setvisimar(chk, mar) {
	var vis = ((chk === true)?1:0);
	window[mar].getStyle().getImage().setOpacity(vis);
	window[mar].changed();
	window[mar].set('visi', vis);
}

function setvisistk(chk, stk) {
	setvisipol(chk, stk);
}


function setvisipol(chk, pol) {
	var vis = ((chk === true)?1:0);
	var hcol = window[pol].get('col');
	window[pol].setStyle(
		new ol.style.Style({
			stroke: new ol.style.Stroke({
			color: [parseInt(hcol.substring(0,2), 16), parseInt(hcol.substring(2,4), 16), parseInt(hcol.substring(4), 16), vis],
			width: polwidth
			})
		})
		);

	window[pol].changed();
	window[pol].set('visi', vis);
}


function isvisib(pol) {
	if (window[pol].get('visi') == 1) return "checked";
	else return "";
}



function dec2dms(dec) {
  dec = Math.abs(dec);
  var decd = Math.floor(dec);
  var decm = Math.floor((dec - decd) * 60);
  var decs = Math.floor((dec - decd - (decm / 60)) * 3600);
  return "" + decd + "&deg; " + decm + "' " + decs + "\"";
}

function changecolor(mark) {
  var colactive = window[mark].get('icol');
	if (++colactive == tcolor.length) colactive = 0;
  var ncol = tcolor[colactive];
	var visib = window[window[mark].get('poly')].get('visi');
	
	
	window[window[mark].get('poly')].setStyle(new ol.style.Style({
					stroke: new ol.style.Stroke({
						//color: '#' + hcol,			// version courte initiale
						color: [parseInt(ncol.substring(0,2), 16), parseInt(ncol.substring(2,4), 16), parseInt(ncol.substring(4), 16), visib ],		// version avec canal alpha pour cacher/afficher
						width: polwidth
					})
					
				}));
	
	
	
  window[mark].set('icol', "" + colactive);
	window[window[mark].get('poly')].set('col', "" + ncol);
  return "#" + ncol;
	
}

function redraw(pol) {
  var p = pol.substring(2);
  var mrk = window["M_" + p];
  var fi = mrk.get('fid');
	var lo = mrk.get('lon');
	
  mrk.set('tra', 1);
  downloadUrl(tld + '/' + cxml1 + '?id=' + p + "&l=" + lo, function(data) {
    var vtrace = data.documentElement.getElementsByTagName("m");
    var err = parseFloat(vtrace[0].getAttribute("e"));
    var idd = vtrace[0].getAttribute("i");
    var encodedt = vtrace[0].getAttribute("r");

    if (err === 0 && encodedt.length > 2) {
			/* ###
      window['P_' + idd].getPath().clear();
      var ftrace = google.maps.geometry.encoding.decodePath(encodedt);
      window['P_' + idd].setPath(ftrace);
			*/
			var format = new ol.format.Polyline({
        //factor: 1e6
			});
			
			var line = format.readGeometry(encodedt, {
        dataProjection: 'EPSG:4326',
        featureProjection: 'EPSG:900913'
			});

			window['P_' + idd].getGeometry().setCoordinates([]);
			window['P_' + idd].setGeometry(line);
			
    }
  });
}


function taskbox() {
  var vtas = false;
  if (document.getElementById('taskbox').checked) {
    vtas = true;
    if (wlt == 2) {
      --wlt;
      reseton();
      resetoff();
    }
  } else {
    if (wlt == 1) {
      ++wlt;
      reseton();
      resetoff();
    }
  }

	taskLayer.setVisible(vtas); 
}


function reclbox() {
  if (document.getElementById('reclbox').checked) {
    vrecl = true;
    rempl(6, "r");
  } else {
    vrecl = false;
    rempl(6, " ");
  }

	receiverLayer.setVisible(vrecl);
  rehash();
}


function checkrec() {
	
  downloadUrl(tld + '/' + rxml, function(data) {
  	if (data == null || data.documentElement == null) {
  		alert(tld + '/' + rxml + ' returned ' + data);
  		return 0;
  	}
    var vlrec = data.documentElement.getElementsByTagName("m");
    var err = parseFloat(vlrec[0].getAttribute("e"));
    if (err === 0 && vlrec.length > 1) {
      selrec = "";
      // effacer markers
      var j = -1;
      while (receivers[++j]) {
				receiverLayerSource.removeFeature(window["R_" + receivers[j][0]]);
        delete window["R_" + receivers[j][0]];
      }
      receivers.length = 0;
      for (var i = 1; i < vlrec.length; i++) {
        var re = vlrec[i].getAttribute("a");
        var rlat = parseFloat(vlrec[i].getAttribute("b"));
        var rlon = parseFloat(vlrec[i].getAttribute("c"));
        var ract = parseInt(vlrec[i].getAttribute("d"));
        var rind = 2000 * ract;
        selrec += "<option value='" + re + "'>" + re + "</option>";
        receivers.push([re, rlat, rlon]); // lat et lon stockÃ©es mais jamais utilisÃ©es ?

				
				window["R_" + re] = new ol.Feature({
					geometry: new ol.geom.Point(ol.proj.fromLonLat([rlon,rlat])),
					lat: rlat,
					lon: rlon,
					mark: "R",
					info: re
				});
				
				window["R_" + re].setStyle(new ol.style.Style({
					image: new ol.style.Icon({
						anchor: [0.5, 1],
						opacity: 1,
						src: "" + tld + "/pict/rec" + ract + ".png",
					})
				}));
				
				receiverLayerSource.addFeature(window["R_" + re]);
      }
      setTimeout(checkrec, 120000);
    } else {
      selrec = "<option value='_error_'>Error</option>";
      setTimeout(checkrec, 20000);
    }
    reclbox();
  });
}




function receiv() {
  if (document.getElementById('recbox').checked) {
    vrec = true;
  } else {
    vrec = false;
  }
}


function affinfodata(mark) {
  var mrk = window[mark];
  var vz = mrk.get('vz') * m2kt[unit];
  var vx = mrk.get('speed') * kh2kt[unit];
  var al = mrk.get('alt') * m2ft[unit];
  document.getElementById("aclt").innerHTML = mrk.get('tim');
  document.getElementById("acla").innerHTML = mrk.get('lat');
  document.getElementById("aclo").innerHTML = mrk.get('lon');
  document.getElementById("acal").innerHTML = al.toFixed() + "&thinsp;" + am2ft[unit];
  document.getElementById("acsp").innerHTML = vx.toFixed() + "&thinsp;" + akh2kt[unit];
  document.getElementById("actr").innerHTML = mrk.get('track');
  document.getElementById("acvz").innerHTML = ((vz >= 0) ? "+" : "&ndash;") + Math.abs(vz).toFixed(1) + "&thinsp;" + am2kt[unit];
	var re = mrk.get('rec');
  var red = "<A HREF='http://ognrange.onglide.com/#" + re + "' target='_blank' onclick=\"event.stopPropagation();\">" + re + "</a>";
  if (typeof(window["R_" + re]) != 'undefined') {
    var mre = window["R_" + re];
    var di = dist(mrk.get('lat'), mrk.get('lon'), mre.get('lat'), mre.get('lon'));
    red += " (" + di.toFixed() + " Km)";
  } else {
    red += " (?)";
  }
  document.getElementById("acrx").innerHTML = red;
}

function affinfodata2(mark) {
  var mrk = window[mark];
  document.getElementById("acmo").innerHTML = mrk.get('model');
}

function affinfo(mark) {
  affinfodata(mark);
  var mrk = window[mark];
  var rg = mrk.get('reg');
  var fi = mrk.get('fid');
  var vd = "block";
  if (fi == rg) vd = "none";
  document.getElementById("ac1").style.display = vd;
  document.getElementById("accn").innerHTML = mrk.get('cn');
  document.getElementById("acre").innerHTML = rg;
  document.getElementById("acty").innerHTML = ftype[mrk.get('type') * 1];
  document.getElementById("acmo").innerHTML = "";
  if (fi != "hidden") {
  	document.getElementById("acfi").innerHTML = "<A HREF='http://www.kisstech.ch/cgi-bin/flarm-txrange.cgi?command=plot&flarmid=" + fi + "' target='_blank' onclick=\"event.stopPropagation();\">" + fi + "</a>";
    document.getElementById("acif").innerHTML = "<A HREF='https://www.google.com/search?nfpr=1&q=\"" + rg + "\"' target='_blank' onclick=\"event.stopPropagation();\">Infos</a>&nbsp;&nbsp;&nbsp;&nbsp;<A HREF='https://www.google.com/search?nfpr=1&q=\"" + rg + "\"&tbm=isch' target='_blank' onclick=\"event.stopPropagation();\">Pictures</a>";
    if (mrk.get('dinfo') === "") {
      downloadUrl(tld + '/' + dxml + '?i=' + mark + '&f=' + fi, function(data) {
        var dat = data.documentElement.getElementsByTagName("m");
        var err = parseFloat(dat[0].getAttribute("g"));
        var mrk = dat[0].getAttribute("i");
        if (err === 0) {
          window[mrk].set('model', "" + dat[0].getAttribute("c"));
          affinfodata2(mrk);
          document.getElementById("ac2").style.display = "block";
          window[mrk].set('dinfo', "ok");
        } else {
          window[mrk].set('dinfo', "_");
          document.getElementById("ac2").style.display = "none";
        }
      });


    } else {
      if (mrk.get('dinfo') != "_") {
        affinfodata2(mark);
        document.getElementById("ac2").style.display = "block";
      } else {
        document.getElementById("ac2").style.display = "none";
      }
    }
  } else {
  	document.getElementById("acfi").innerHTML = fi;
    document.getElementById("ac2").style.display = "none";
    document.getElementById("acif").innerHTML = "";
    document.getElementById("acmo").innerHTML = "";
  }
  acaff = mark;
  document.getElementById("ac").style.display = "block";
}

function settomap() {
	
	
	var extent = map.getView().calculateExtent(map.getSize());
  var bottomLeft = ol.proj.transform(ol.extent.getBottomLeft(extent),'EPSG:3857', 'EPSG:4326');
	var topRight = ol.proj.transform(ol.extent.getTopRight(extent),'EPSG:3857', 'EPSG:4326');

	amax = topRight[1];
  amin = bottomLeft[1];
	omax = topRight[0];
	omin = bottomLeft[0];
	
  if (amax > 85) amax = 85;
  if (amin < -85) amin = -85;
  if (omax > 180) omax = 180;
  if (omin < -180) omin = -180;
  document.getElementById('latmax').value = amax;
  document.getElementById('latmin').value = amin;
  document.getElementById('lonmax').value = omax;
  document.getElementById('lonmin').value = omin;
  if (bound === true) bounds();
  if (vstm === true) {
    boundc = "&b=" + amax + "&c=" + amin + "&d=" + omax + "&e=" + omin;
    hashs = "&s=1";
    rehash();
  }

}

function astm() {
  if (document.getElementById('astmbox').checked) {
    vstm = true;
    if (document.getElementById('boundsbox').checked) {
      bound = false;
      document.getElementById('boundsbox').checked = false;
      hashb = "";
    }
    settomap();

  } else {
    vstm = false;
    if (bound === false) boundc = "";
    hashs = "";
    rehash();
  }
}

function dist(lat1, lon1, lat2, lon2) {
  var torad = Math.PI / 180;
  lat1 *= torad;
  lon1 *= torad;
  lat2 *= torad;
  lon2 *= torad;
  var dt = Math.acos((Math.sin(lat1) * Math.sin(lat2)) + (Math.cos(lat1) * Math.cos(lat2) * Math.cos(lon1 - lon2)));
  dt *= 6366;
  return dt;
}

function baro_reSize() {
  switch(pathl) {
    case 30: 
      document.getElementById('dbaro').style.width = "155px"; // 70+85
	  // weird behaviour for canvas sizing versus scaling
      document.getElementById('div_baro').style.width = "70px";
      document.getElementById('div_baro').width = 70;
	  X_lines = 5+1;
	  break;
    case 60: 
      document.getElementById('dbaro').style.width = "225px"; // 140+85
	  // weird behaviour for canvas sizing versus scaling
      document.getElementById('div_baro').style.width = "140px";
      document.getElementById('div_baro').width = 140;
	  X_lines = 10+1;
	  break;
	default:  
      document.getElementById('dbaro').style.width = "295px" ; //210+85
	  // weird behaviour for canvas sizing versus scaling
      document.getElementById('div_baro').style.width = "210px";
      document.getElementById('div_baro').width = 210;
	  X_lines = 15+1;
  }
}

function baro_plot() {

  var j = -1;
  while (online[++j]) {
	// * if (window["P_" + online[j][2]].getVisible() === true) {
		if (window["P_" + online[j][2]].get('visi') == 1) {
			baro_plotData(online[j][0],online[j][3],window["B_" + online[j][2]]);
		}	
  }

}

function gesmark() {
  if (nbreq > 0) {
    --nbreq;
    return;
  }

  ++nbreq;
  downloadUrl(tld + '/' + cxml + "?a=" + all + boundc + recc + parc + tz + hashy, function(data) {
    ++w;
  	if (data == null || data.documentElement == null) {
  		alert(tld + '/' + cxml + ' returned ' + data);
  		return 0;
  	}
    var planeurs = data.documentElement.getElementsByTagName("m");
    online.length = 0;
    offline.length = 0;
    var colcn;
    var del = "N";

    for (var i = 0; i < planeurs.length; i++) {
      // rÃ©cupÃ©ration des donnÃ©es transmises pour ce planeur
      var tab = planeurs[i].getAttribute("a").split(",");


      var fid = tab[12];
      if (wlt == 1) {
        if (wlist.indexOf(fid) == -1) continue;
      }
      var ps = tab[3];
      var lat = parseFloat(tab[0]);
      var lon = parseFloat(tab[1]);
      var cn = tab[2];
      if (cn == "") cn = "_";

      var alt = tab[4];
      var tim = tab[5];
      var ddf = tab[6];
      var track = tab[7];
      var speed = tab[8];
      var vz = tab[9];
      var typ = tab[10];
      var rec = tab[11];

      var crc = tab[13];

		
			var posi = new ol.geom.Point(ol.proj.fromLonLat([lon,lat]));
      var te = 0; //altitude sol
//      elevator.getElevationForLocations({'locations': [posi]}, function(results, status) {
//      if (status == google.maps.ElevationStatus.OK) {
//          if (results[0]) {
//            te = Math.round(results[0].elevation);
//          }
//        }
//      });
			var posiBaton = new ol.geom.Point(ol.proj.fromLonLat([lon,lat+(0.00001*(alt-te))]));
			
			
      var polyvar = "P_" + crc;
      var markvar = "M_" + crc;
      var stickvar = "S_" + crc;
      var barovar = "B_" + crc;
			var visib = 1;


      if (typeof(window[polyvar]) == 'undefined') // If aircraft not already created
      {
        // create path color for array
        hcol = tcolor[ccolor];
        if (hnew === true) visib = 0; // * false;

        // create polyline
				
				window[polyvar] = new ol.Feature({
					geometry: new ol.geom.LineString([ol.proj.fromLonLat([lon,lat])])
				});
				window[polyvar].setStyle(new ol.style.Style({
					stroke: new ol.style.Stroke({
						//color: '#' + hcol,			// version courte initiale
						color: [parseInt(hcol.substring(0,2), 16), parseInt(hcol.substring(2,4), 16), parseInt(hcol.substring(4), 16), visib ],		// version avec canal alpha pour cacher/afficher
						width: polwidth
					})
					
				}));
				traceLayerSource.addFeature(window[polyvar]);
				window[polyvar].set('poly', "" + polyvar);
				window[polyvar].set('visi', visib);
				window[polyvar].set('col', "" + hcol);
				window[polyvar].set('nom', "" + cn + " - " + ps);
			
				
				        // crÃ©ation du Baton d'altitude

				
				window[stickvar] = new ol.Feature({
					geometry: new ol.geom.LineString([ol.proj.fromLonLat([lon,lat])])
				});
				window[stickvar].setStyle(new ol.style.Style({
					stroke: new ol.style.Stroke({
						color: [0, 0, 0, visib ],		// version avec canal alpha pour cacher/afficher // black for now
						// color: [parseInt(hcol.substring(0,2), 16), parseInt(hcol.substring(2,4), 16), parseInt(hcol.substring(4), 16), visib ],		// version avec canal alpha pour cacher/afficher
						width: polwidth
					})
					
				}));
				window[stickvar].set('nom', "" + cn + " - " + ps);
        window[stickvar].set('baton', "" + stickvar);
				window[stickvar].set('col', "000000");		// stick color is black
				sticksLayerSource.addFeature(window[stickvar]);

        // crÃ©ation du Marker
				
				
					
				window[markvar] = new ol.Feature({
					geometry: posi,
					title: cn + " - " + ps + " @ " + alt + "m",
	//				id: markvar
					lat: lat,
					lon: lon
				});
				
				window[markvar].setStyle(new ol.style.Style({
					image: new ol.style.Icon({
						anchor: [0.5, 1],
						opacity: visib,
						src: "" + tld + "/markers/" + cn + ftypec[typ * 1] + ".png"
					})
				}));
				
				window[markvar].set('poly', "" + polyvar);
        window[markvar].set('mark', "" + markvar);
        window[markvar].set('stick', "" + stickvar);
        window[markvar].set('nom', "" + cn + " - " + ps);
        window[markvar].set('cn', "" + cn);
        window[markvar].set('reg', "" + ps);
        if (fid == "0") fid = "hidden";
        window[markvar].set('fid', "" + fid);
        window[markvar].set('type', "" + typ);
        window[markvar].set('icol', "" + ccolor);
        window[markvar].set('off', 0);
        window[markvar].set('dinfo', "");
        // * window[markvar].setTitle("" + cn + " - " + ps + " @ " + (alt * m2ft[unit]).toFixed() + am2ft[unit] + " @ " + tim);
        window[markvar].set('speed', "" + speed);
        window[markvar].set('track', "" + track);
        window[markvar].set('vz', "" + vz);
        window[markvar].set('tim', "" + tim);
        window[markvar].set('rec', "" + rec);
        window[markvar].set('alt', "" + alt);
        window[markvar].set('tra', 0);
				window[markvar].set('visi', visib);
				
				iconLayerSource.addFeature(window[markvar]);
				
        /* ###
				google.maps.event.addListener(window[markvar], "mouseover", function() {
          var bcol = window[this.get('poly')].strokeColor;
          document.getElementById("divInfo").innerHTML = "<span style='background-color: " + bcol + "'>&nbsp;&nbsp;&nbsp;</span>&nbsp;" + this.get('nom');
          focuson(this.get('poly'));
//          focuson(this.get('stick'));
        });

        google.maps.event.addListener(window[markvar], "mouseout", function() {
          document.getElementById("divInfo").innerHTML = "&nbsp;";
          focusoff(this.get('poly'));
//          focusoff(this.get('stick'));
        });

        google.maps.event.addListener(window[markvar], "click", function() {
          affinfo(this.get('mark'));
        });

        google.maps.event.addListener(window[markvar], "dblclick", function() {
          document.getElementById("divInfoac").innerHTML = "<B>AC</B>: " + this.get('title');
          autoc = this.get('mark');
          document.getElementById("divInfoac").style.display = "block";
          map.setCenter(this.position);
        });

        google.maps.event.addListener(window[markvar], "rightclick", function() {
          var pol = this.get('poly');
          redraw(pol);
        });
				*/

        // create array and add barogram time and altitude
				window[barovar] = [];
				window[barovar].push([tim.toSeconds(),alt]);
				// reset the time scale on the barogram
				Set_XY_Scale(tim,alt);

        if (++ccolor == tcolor.length) ccolor = 0;
      } // fin du if typeof...

      var difalt = vz * 1;

			colcn = window[polyvar].get('col');

      if (ddf < 600) { // if online (active during 10 last minutes)
        if (ddf > 120) afdif = "n";
        else if (difalt === 0) afdif = "z";
        else if (difalt < -4) afdif = "mmm";
        else if (difalt < -1) afdif = "mm";
        else if (difalt < 0) afdif = "m";
        else if (difalt > 4) afdif = "ppp";
        else if (difalt > 1) afdif = "pp";
        else afdif = "p";

        
				
				online.push([cn, alt * 1, crc, '#'+colcn, afdif]);
				
				if (window[markvar].get('off') == 1) {
					window[markvar].setStyle(new ol.style.Style({
							image: new ol.style.Icon({
								anchor: [0.5, 1],
								src: "" + tld + "/markers/" + cn + ftypec[typ * 1] + ".png"
							})
					}));
					window[markvar].set('off', 0);
					window[markvar].changed();
					map.render();
				}
				
				if (window[markvar].get('tra') === 0) {  // partial path, not whole path
          // * if (window[polyvar].getPath().getLength() >= pathl) window[polyvar].getPath().removeAt(0); // remove first point of the trace
					if (window[polyvar].getGeometry().getCoordinates().length >= pathl) {
						window[polyvar].getGeometry().setCoordinates(	window[polyvar].getGeometry().getCoordinates().slice(1) );
					}
        }

        // * window[polyvar].getPath().push(posi); // ajout d'une position sur le tracÃ©
				window[polyvar].getGeometry().appendCoordinate(ol.proj.fromLonLat([lon, lat]));
				window[polyvar].changed();
				map.render();

				
				if (typeof(window[markvar]) != 'undefined') {
					if (stick === 1) {

						window[stickvar].getGeometry().setCoordinates([ol.proj.fromLonLat([lon,lat]),ol.proj.fromLonLat([lon,lat+(0.00001*(alt-te))])]);
						window[markvar].setGeometry(posiBaton); // dÃ©place le marker							

						
					} else {
						
						try {
							window[markvar].setGeometry(posi); // dÃ©place le marker							
						}
						catch(err) {
							console.log("err maj posi du marker " + markvar + " : " + err.message);
						}
						
					}
					window[markvar].changed();
					map.render();
					

					// change l'altitude affichÃ©e

					// * window[markvar].setTitle("" + cn + " - " + ps + " @ " + (alt * m2ft[unit]).toFixed() + am2ft[unit] + " @ " + tim);
					window[markvar].set('title', "" + cn + " - " + ps + " @ " + (alt * m2ft[unit]).toFixed() + am2ft[unit] + " @ " + tim);
					window[markvar].set('speed', "" + speed);
					window[markvar].set('track', "" + track);
					window[markvar].set('vz', "" + vz);
					window[markvar].set('tim', "" + tim);
					window[markvar].set('rec', "" + rec);
					window[markvar].set('alt', "" + alt);
					window[markvar].set('lat', lat);
					window[markvar].set('lon', lon);
				}
				

	// check display time and remove old data
        if (window[barovar].length >= pathl) window[barovar].shift(); // remove first point of the trace
	// add barogram data
				window[barovar].push([tim.toSeconds(),alt]);
        Set_XY_Scale(tim,alt);

      } else {		// offline
        if (all === 0) {			// if offline not displayed
          // if (typeof(window[polyvar]) != 'undefined') { // si pas dÃ©jÃ  effacÃ©
					if (typeof(window[markvar]) != 'undefined') { // si pas dÃ©jÃ  effacÃ©
//          // efface et dÃ©truit le PolyLine et le Marker
            // efface et dÃ©truit le baton, le PolyLine et le Marker

            /// ### window[stickvar].setMap(null);
            delete window[stickvar];
						
						delete window[barovar];
								  
						iconLayerSource.removeFeature(window[markvar]);
						traceLayerSource.removeFeature(window[polyvar]);
						map.render();
            delete window[markvar];
						delete window[polyvar];
		  
            if (autoc == markvar) {
              autoc = "";
              document.getElementById("divInfoac").innerHTML = "&nbsp;";
              document.getElementById("divInfoac").style.display = "none";
            }
            if (acaff == markvar) acaff = "";

          }
        } else {				// if offline displayed
          offline.push([cn, alt * 1, crc, '#'+colcn, "n"]);
          if (window[markvar].get('off') === 0) {
						/* ###
            window[markvar].setOptions({
              zIndex: 10
            });
						*/

						window[markvar].setStyle(new ol.style.Style({
							image: new ol.style.Icon({
								anchor: [0.5, 1],
								src: "" + tld + "/markers/" + cn + "_o.png"
							})
						}));
						window[markvar].set('off', 1);
						window[markvar].changed();
						map.render();
          }
        }
      }


      if (autoc == markvar) {
        document.getElementById("divInfoac").innerHTML = "<B>AC</B>: " + cn + " - " + ps + " @ " + (alt * m2ft[unit]).toFixed() + am2ft[unit];
        if (cton === false) map.getView().setCenter(ol.proj.transform([lon, lat], 'EPSG:4326', 'EPSG:3857'));
      }

     if (acaff == markvar) affinfodata(markvar);


    } // fin du for (var i = 0; i < planeurs.length; i++)
    // tri et affichage du tableau
	
    afftab();
	
    baro_plotRefresh();
    baro_plot();

    if (--nbreq < 0) {
      nbreq = 0;
    } else {
      tmgm = setTimeout(gesmark, 10000);
    }
  });

}

function wd() {
  if (w === 0) {
    clearTimeout(tmgm);
    gesmark();
  }
  w = 0;
  tmwd = setTimeout(wd, 30000);
}

function rehash() {
//  window.location.replace("#" + hashc + hashz + hashm + hasho + hashb + hashs + hashl + hashw + hashp + hashu + hashn + hashy);
  window.location.replace("#" + hashc + hashz + hashm + hasho + hashb + hashs + hashl + hashw + hashp + hashu + hashn + hashy + hasha + hashg);
}

function rempl(po, c) {
  var thl = hl;
  hl = thl.substring(0, po) + c + thl.substring(po + 1);
  thl = hl.replace(/ /g, '');
  if (thl === '') hashl = '';
  else hashl = "&l=" + thl;
}

function taskclic() {
  document.getElementById("chfile").click();
}

function loadtask(cont) {
  var tasks = [];
  try {
    tasks = tasks.concat(parseJSONTasks(cont));
  } catch (err) {
    tasks.push(parseXCSoarTask(cont));
  }

  for (var i = 0; i < tasks.length; i++) {
    showTask(tasks[i]);
    filterDevices(tasks[i].wlist);
  }
	taskLayer.setVisible(true);
}

function parseJSONTasks(cont) {
  var res = JSON.parse(cont);

  var tasks = [];

  for (var i = 0; i < res.tasks.length; i++) {
    var task = {};
    task.name = res.tasks[i].name;
    task.color = res.tasks[i].color;

    var tp = [];
    if (typeof res.tasks[i].legs != 'undefined') {
      for (var ii = 0; ii < res.tasks[i].legs.length; ii++) {
        if (typeof res.tasks[i].legs[ii][1] == 'undefined') { // circle
          tp[tp.length - 1].type = "circle";
          tp[tp.length - 1].radius = res.tasks[i].legs[ii][0];
        } else {
          tp.push({
            lat: res.tasks[i].legs[ii][0],
            lon: res.tasks[i].legs[ii][1]
          });
        }
      }
    }
    task.turnpoints = tp;

    if (typeof res.tasks[i].wlist != 'undefined') {
      task.wlist = [];
      for (var ii = 0; ii < res.tasks[i].wlist.length; ii++) {
        task.wlist.push(res.tasks[i].wlist[ii]);
      }
    }
    tasks.push(task);
  }
  return tasks;
}

function parseXCSoarTask(cont) {
  var ltp;
  var tp = [];
  var wl = [];

  tp.length = 0;

  var oParser = new DOMParser();
  var oDOM = oParser.parseFromString(cont, "text/xml");

  var points = oDOM.getElementsByTagName("Point");
  for (var i = 0; i < points.length; i++) {
    var loc = points[i].getElementsByTagName("Waypoint")[0].getElementsByTagName("Location")[0];
    var ltp = {
      lat: loc.getAttribute("latitude"),
      lon: loc.getAttribute("longitude")
    };

    if (points[i].getElementsByTagName("ObservationZone")[0].getAttribute("type") == "Cylinder") {
      ltp.type = "circle";
      ltp.radius = parseFloat(points[i].getElementsByTagName("ObservationZone")[0].getAttribute("radius"));
    }
    tp.push(ltp);
  }

  var task = {
    turnpoints: tp
  };
  return task;
}

function showTask(task) {

  var tc, tn, ltp;
  var tp = [];

  tn = task.name || 'task ' + task.length;
  tc = task.color || 'FF0000';

  for (var ii = 0; ii < task.turnpoints.length; ii++) {
    if ((task.turnpoints[ii].type == 'circle')) {
			
					
			var cc = ol.geom.Polygon.circular(
					/* WGS84 Sphere */
					new ol.Sphere(6378137),
					[task.turnpoints[ii].lon, task.turnpoints[ii].lat],
					task.turnpoints[ii].radius,
					/* Number of verticies */
					64
					);
			cc.transform('EPSG:4326', 'EPSG:3857');
			
			var circle = new ol.Feature({
        geometry: cc
			});

			circle.setStyle(new ol.style.Style({
				    stroke: new ol.style.Stroke({
            color: '#' + tc,
            width: polwidth
        }),
        fill: new ol.style.Fill({
					color: [parseInt(tc.substring(0,2), 16), parseInt(tc.substring(2,4), 16), parseInt(tc.substring(4), 16), 0.1 ]
        })
			}));

			taskLayerSource.addFeature(circle);
			
    }
		point = ol.proj.fromLonLat([task.turnpoints[ii].lon, task.turnpoints[ii].lat]);
     tp.push(point);
    
  }
	
	var taskpath = new ol.Feature({
					geometry: new ol.geom.LineString( tp )
				});
	taskpath.setStyle(new ol.style.Style({
		stroke: new ol.style.Stroke({
			color: '#' + tc,
			width: polwidth
		})
	}));
	taskpath.set('nom', '' + tn);
  
	taskLayerSource.addFeature(taskpath);
	
	// ### Ã  mettre ailleurs car appelÃ© a chaque task du fichier
  document.getElementById('dtaskbox').innerHTML = '<INPUT type="checkbox" id="taskbox" onChange="javascript : taskbox();" checked>';

}

function filterDevices(wl) {
  if (typeof wl != 'undefined') {
    for (var i = 0; i < wl.length; i++) {
      wlist.push(wl[i]);
    }
  }

  if (wlist.length > 0) {
    wlt = 1;

    reseton();
    resetoff();
  }
}

function rtask() { // select a task file
  var files = document.getElementById('chfile').files;
  if (!files.length) {
    alert('Please select a file!');
    return;
  }
  var file = files[0];
  var reader = new FileReader();
  reader.onloadend = function(evt) {
    if (evt.target.readyState == FileReader.DONE) {
      var cont = evt.target.result;
      cont = cont.trim();
      loadtask(cont);
    }
  };
  reader.readAsText(file);
}


function initialize() {
  var has = window.location.hash.substring(1).split('&'); // parse the parameters
  var parh = [];
  var cent = [];
  var gmdelay = 0; // to delay first call to gesmark if task file required
  for (var i = 0; i < has.length; i++) {
    var x = has[i].split('=');
    parh[x[0]] = x[1];
  }

  // parameter c=lat,lon (center of the map)
  if (typeof(parh.c) != 'undefined') {
    cent = parh.c.split(',');
    vlat = parseFloat(cent[0]);
    vlon = parseFloat(cent[1]);
    hashc = "c=" + vlat.toFixed(5) + "," + vlon.toFixed(5);
  }

  // parameter o=1 (display offline)
  if (typeof(parh.o) != 'undefined') {
    if (parh.o == "1") {
      all = 1;
      hasho = "&o=1";
    }
  }

	airspaceoverlay = new ol.layer.Tile({
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
	
	airportoverlay = new ol.layer.Tile({
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
	
  windoverlay = new ol.layer.Tile({
      source: new ol.source.XYZ({
				/*
        tileUrlFunction: function(tileCoord, projection) {
          var z = tileCoord[0];
          var x = tileCoord[1];
          var y = (1 << z) + tileCoord[2];
          return "http://weather.openportguide.de/tiles/actual/wind_stream/0h/" + z + "/" + x + "/" + y + ".png";
        },
				*/
				url: 'http://weather.openportguide.de/tiles/actual/wind_stream/0h/{z}/{x}/{y}.png',
        wrapx: false
      }),
      opacity: 1,
      visible: false
    });

  presoverlay = new ol.layer.Tile({
      source: new ol.source.XYZ({
				/*
        tileUrlFunction: function(tileCoord, projection) {
          var z = tileCoord[0];
          var x = tileCoord[1];
          var y = (1 << z) + tileCoord[2];
          return "http://weather.openportguide.de/tiles/actual/surface_pressure/0h/" + z + "/" + x + "/" + y + ".png";
        },
				*/
				url: 'http://weather.openportguide.de/tiles/actual/surface_pressure/0h/{z}/{x}/{y}.png',
        wrapx: false
      }),
      opacity: 1,
      visible: false
    });

  tempoverlay = new ol.layer.Tile({
      source: new ol.source.XYZ({
				/*
        tileUrlFunction: function(tileCoord, projection) {
          var z = tileCoord[0];
          var x = tileCoord[1];
          var y = (1 << z) + tileCoord[2];
          return "http://weather.openportguide.de/tiles/actual/air_temperature/0h/" + z + "/" + x + "/" + y + ".png";
        },
				*/
				url: 'http://weather.openportguide.de/tiles/actual/air_temperature/0h/{z}/{x}/{y}.png',
        wrapx: false
      }),
      opacity: 1,
      visible: false
    });

  rainoverlay = new ol.layer.Tile({
      source: new ol.source.XYZ({
				/*
        tileUrlFunction: function(tileCoord, projection) {
          var z = tileCoord[0];
          var x = tileCoord[1];
          var y = (1 << z) + tileCoord[2];
          return "http://weather.openportguide.de/tiles/actual/precipitation_shaded/0h/" + z + "/" + x + "/" + y + ".png";
        },
				*/
				url: 'http://weather.openportguide.de/tiles/actual/precipitation_shaded/0h/{z}/{x}/{y}.png',
        wrapx: false
      }),
      opacity: 0.4,
      visible: false
    });

	OSMLayer = new ol.layer.Tile({
    source: new ol.source.OSM(),
    visible: true
  });
		
	
  MapsForFreeLayer = new ol.layer.Tile({
      source: new ol.source.XYZ({
				attributions: [
          new ol.Attribution({
            html: '<br>Background map: Maps-For-Free.com<br>'
          })
        ],
        url: 'https://maps-for-free.com/layer/relief/z{z}/row{y}/{z}_{x}-{y}.jpg',

        wrapx: false
      }),
      opacity: 1,
      visible: false
    });
		
  MapsForFreeLayerW = new ol.layer.Tile({
      source: new ol.source.XYZ({
        url: 'https://maps-for-free.com/layer/water/z{z}/row{y}/{z}_{x}-{y}.gif',
        wrapx: false
      }),
      opacity: 1,
      visible: false
    });	
		
	OSMTopoLayer = new ol.layer.Tile({
      source: new ol.source.XYZ({
				attributions: [
          new ol.Attribution({
            html: '<br>Background map: <A HREF="https://opentopomap.org" target="_blank">OpenTopoMap</A><br>'
          })
        ],
				url: '//{a-c}.tile.opentopomap.org/{z}/{x}/{y}.png',
        wrapx: false
      }),
      opacity: 1,
      visible: false
    });
			
		
	IGNSatelliteLayer = new ol.layer.Tile({
      source: new ol.source.XYZ({
				attributions: [
          new ol.Attribution({
            html: '<br>Background map: <A HREF="http://www.geoportail.gouv.fr/depot/api/cgu/CGU_API_libre.pdf" target="_blank">IGN</A><br>'
          })
        ],
				url: '//wxs.ign.fr/pratique/wmts/?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image%2Fjpeg',
        wrapx: false
      }),
      opacity: 1,
      visible: false
    });
				

		
	iconLayerSource = new ol.source.Vector({
		attributions: [
      new ol.Attribution({html:'<br>Powered by <a href="http://glidernet.org" target="_blank">Open Glider Network</a>'})
		],
		features: []
	});
	
	iconLayer = new ol.layer.Vector({	
			source: iconLayerSource,
			zIndex: 200
			});

			
	sticksLayerSource = new ol.source.Vector({
			features: []
			});
	
	sticksLayer = new ol.layer.Vector({	
			source: sticksLayerSource,
			zIndex: 150,
			opacity: 1,
			visible: false
			});			
	
	traceLayerSource = new ol.source.Vector({
			features: []
			});
	
	traceLayer = new ol.layer.Vector({	
			source: traceLayerSource,
			zIndex: 100
			});
			
	taskLayerSource = new ol.source.Vector({
			features: []
			});
	
	taskLayer = new ol.layer.Vector({	
			source: taskLayerSource,
			zIndex: 70
			});
			
			
	receiverLayerSource = new ol.source.Vector({
			features: []
			});
	
	receiverLayer = new ol.layer.Vector({	
			source: receiverLayerSource,
			zIndex: 50,
			opacity: 1,
      visible: false
			});
	
  attribution = new ol.control.Attribution({
        collapsed: true,
				tipLabel: 'Show credits'
      });
	
	scaleLineControl = new ol.control.ScaleLine();		
	
	
			
	map = new ol.Map({
        interactions: ol.interaction.defaults().extend([
          new ol.interaction.DragRotateAndZoom()
        ]),
        layers: [
					MapsForFreeLayer,
					MapsForFreeLayerW,
					OSMTopoLayer,
					IGNSatelliteLayer,
					OSMLayer,
					receiverLayer,
					airportoverlay,
					airspaceoverlay,
					windoverlay,
					presoverlay,
					tempoverlay,
					rainoverlay,
					taskLayer,
					traceLayer,
					sticksLayer,
					iconLayer
        ],
        target: 'map_canvas',
        controls: ol.control.defaults({
          attributionOptions: {
            //collapsible: false
						collapsible: true
          }
        }).extend([
					scaleLineControl,
					attribution
        ]),
        view: new ol.View({
          center: ol.proj.fromLonLat([vlon,vlat]),
          zoom: 10
        })
      });
	
  map.on('singleclick', function(event) {
		var receiver = false;
		var recinfo = "";
		var coord;
    map.forEachFeatureAtPixel(event.pixel, function(feature,layer) {
			if(typeof(feature.get('mark'))!='undefined'){
        if ( feature.get('mark').substring(0,1) == "M" ) {
					affinfo(feature.get('mark'));
					document.getElementById('lonlatoverlay').style.display = "none";
					return;
        }
				if ( feature.get('mark').substring(0,1) == "R" ) {
					receiver = true;
					recinfo = feature.get("info");
					coord = feature.getGeometry().getCoordinates();
				}
			}
    });
		if (receiver) {
			document.getElementById("lonlatoverlay").innerHTML = recinfo;
			lonlatoverlay.setPosition(coord);
			document.getElementById('lonlatoverlay').style.display = "block";
		} else
			document.getElementById('lonlatoverlay').style.display = "none";
	});
	
	map.on('moveend', function(event) {
		// get zoom level
    hashz = "&z=" + map.getView().getZoom();
		
		// get center
		var nc = ol.proj.toLonLat( map.getView().getCenter() );
    hashc = "c=" + nc[1].toFixed(5) + "," + nc[0].toFixed(5);
		
		// get rotate
		var rotation = map.getView().getRotation();
		if (rotation == 0) {
			document.getElementById('NorthButton').style.display = "none";
		} else {
			document.getElementById('NorthButton').style.display = "block";
			document.getElementById('NorthButton').style.transform = "rotate("+ rotation +"rad)";
		}
		
    rehash();
		
		if (vstm === true) settomap();
		
		document.getElementById('lonlatoverlay').style.display = "none";
  });
	
	map.on('pointermove', function(event) {
		var changed = false;
    map.forEachFeatureAtPixel(event.pixel, function(feature,layer) {
			if(typeof(feature.get('col'))!='undefined'){
				lastpol = feature.get('poly');
				focuson(lastpol);
				document.getElementById("divInfo").innerHTML = "<span style='background-color: #" + feature.get('col') + "'>&nbsp;&nbsp;&nbsp;</span>&nbsp;" + feature.get('nom');
				changed = true;
				return;
      }
    });
		if (!changed) {
			focusoff(lastpol);
			document.getElementById("divInfo").innerHTML = " ... ";
		}


	});
	
	map.getViewport().addEventListener('contextmenu', function (evt) {
    evt.preventDefault();
		var nb = 0;
		map.forEachFeatureAtPixel([evt.layerX,evt.layerY], function(feature,layer) {
			++nb;
      if ( feature.get('mark').substring(0,1) == "M" ) {
			redraw('P_' + feature.get('mark').substring(2));
      }
    });
		
		if (nb == 0) {
			var coord = map.getEventCoordinate(evt);
			// transform it to decimal degrees
			var degrees = ol.proj.transform(coord, 'EPSG:3857', 'EPSG:4326');
			// format a human readable version
			var hdms = ol.coordinate.toStringHDMS(degrees);
			// update the overlay element's content
			document.getElementById("lonlatoverlay").innerHTML = hdms;
			// position the element (using the coordinate in the map's projection)
			lonlatoverlay.setPosition(coord);
			document.getElementById('lonlatoverlay').style.display = "block";
			
		}
		
		
		
	});
	
	northbutton = document.createElement('button');
	northbutton.setAttribute("id", "NorthButton");
	northbutton.style.display = "none";
	northbutton.innerHTML = '&uarr;';

	handleRotateNorth = function(e) {
    map.getView().setRotation(0);
	};

	// add button to rotate noth up
	northbutton.addEventListener('click', handleRotateNorth, false);

	// add button to switch map	
	mapbutton = document.createElement('button');
	mapbutton.innerHTML = 'M';
	map_selector = function(e) {		// select map layer
		if (++map_id == 4) map_id = 0;
		chmap(map_id);
  }
	
	mapbutton.addEventListener('click', map_selector, false);
	
	
	divInfo = document.createElement("div");
  divInfo.id = "divInfo";
  divInfo.className = "divInfoclass";
  divInfo.style.width = "120px";
  divInfo.style.float = "left";
  divInfo.style.display = "block";

  divInfo.appendChild(document.createTextNode("..."));

	zoomdiv = document.getElementsByClassName('ol-zoom ol-unselectable ol-control')[0];
	zoomdiv.appendChild(mapbutton);
	zoomdiv.appendChild(northbutton);
	zoomdiv.appendChild(divInfo);
	
	// displays credits over the list
	credits = document.getElementsByClassName('ol-attribution ol-unselectable ol-control')[0];
	credits.style.zIndex = "1000";
		
	// parameter m= map type
	if (typeof(parh.m) != 'undefined') {
		map_id = parseInt(parh.m);
		chmap(map_id);
    hashm = "&m=" + map_id;
  }


	


	/* *
  // parameter z=  zoom level
  if (typeof(parh.z) != 'undefined') map.setZoom(parseInt(parh.z));
	*/ 
	if (typeof(parh.z) != 'undefined') map.getView().setZoom(parseInt(parh.z));
	/* ###
  else {
    var southWest = new google.maps.LatLng(vlatmin, vlonmin);
    var northEast = new google.maps.LatLng(vlatmax, vlonmax);
    var bounds = new google.maps.LatLngBounds(southWest, northEast);
    map.fitBounds(bounds);
  }

	*/

	// overlay to display coordinate on a right-clic
	lonlatoverlay = new ol.Overlay({
    element: document.getElementById('lonlatoverlay'),
    positioning: 'bottom-center'
    });
			
	map.addOverlay(lonlatoverlay);
	

	
	/* ###

  var divinfoContac = document.createElement('DIV'); // contener autocenter
  divinfoContac.style.paddingTop = "7px";
  divinfoContac.style.paddingRight = "3px";

  var divinfoContpb = document.createElement('DIV'); // contener poweredby
  divinfoContpb.style.paddingTop = "7px";
  divinfoContpb.style.paddingRight = "3px";

	*/
	
	/* *
  var divInfo = document.createElement("div");
  divInfo.id = "divInfo";
  divInfo.className = "divInfoclass";
  divInfo.style.width = "170px";
  divInfo.style.float = "left";
  divInfo.style.display = "block";

  divInfo.appendChild(document.createTextNode("..."));
	
	*/
	
	/* ###

  var divInfoac = document.createElement("div");
  divInfoac.id = "divInfoac";
  divInfoac.className = "divInfoclass";
  divInfoac.style.width = "170px";
  divInfoac.style.cursor = 'pointer';
  divInfoac.style.float = "left";
  divInfoac.style.display = "none";

  divInfoac.appendChild(document.createTextNode("..."));

  var divInfopb = document.createElement("div");
  divInfopb.id = "divInfopb";
  //divInfopb.className = "divInfoclass";
  //divInfopb.style.width = "170px";
  divInfopb.style.backgroundColor = '#F5F5F5';
  divInfopb.style.opacity = 0.7;

  divInfopb.style.cursor = 'pointer';
  divInfopb.style.float = "left";
  divInfopb.style.display = "block";
  divInfopb.innerHTML = "&nbsp;&nbsp;Powered By <A HREF=\"http://glidernet.org\" target=\"_blank\"><B>GliderNet.Org</B></A>&nbsp;&nbsp;";


  // divInfopb.appendChild ( document.createTextNode("Powered By <B>GliderNet.Org</B>"));


  divinfoCont.appendChild(divInfo);
  divinfoContac.appendChild(divInfoac);
  divinfoContpb.appendChild(divInfopb);

  divinfoCont.index = 1;
	*/
	
	/* ###
  map.controls[google.maps.ControlPosition.TOP_CENTER].push(divinfoCont);
  map.controls[google.maps.ControlPosition.TOP_LEFT].push(divinfoContac);
  map.controls[google.maps.ControlPosition.TOP_RIGHT].push(divinfoContpb);

  google.maps.event.addDomListener(divInfoac, 'click', function() {
    document.getElementById("divInfoac").innerHTML = "&nbsp;";
    autoc = "";
    document.getElementById("divInfoac").style.display = "none";
  });




  // affiche l'altitude du terrain quand clic-droit
  elevator = new google.maps.ElevationService();
  google.maps.event.addListener(map, 'rightclick', function(event) {
    var locations = [];
    var clickedLocation = event.latLng;
    locations.push(clickedLocation);

    var latc = clickedLocation.lat();
    var alat = (latc >= 0 ? "N" : "S") + " " + dec2dms(latc);

    var lonc = clickedLocation.lng();
    var alon = (lonc >= 0 ? "E" : "W") + " " + dec2dms(lonc);

    var positionalRequest = {
      'locations': locations
    };

    elevator.getElevationForLocations(positionalRequest, function(results, status) {
      if (status == google.maps.ElevationStatus.OK) {
        if (results[0]) {
          var te = Math.round(results[0].elevation);
          infowindow.setContent('Elevation:' + (te * m2ft[unit]).toFixed() + am2ft[unit] + '<BR>Lat: ' + alat + '<BR>Lon: ' + alon);
          infowindow.setPosition(clickedLocation);
          infowindow.open(map);
        } else {
          alert('No results found');
        }
      } else {
        alert('Elevation service failed due to: ' + status);
      }
    });
  });

	*/
	
  document.getElementById("ett1").innerHTML = ett1;
  document.getElementById("ett2").innerHTML = "<TABLE class=\"tt\"><TR width=\"12\"><TH class=\"cgv\" ondblclick=\"allmarker();\"><IMG src='" + tld + "/pict/ico.png'></TH><TH class=\"cgv\" ondblclick=\"allpath();\"><IMG src='" + tld + "/pict/tra.gif'></TH><TH class=\"cgn\" onclick=\"tricn();\">CN</TH><TH class=\"cgc\" ondblclick=\"deleteallpath();\"><IMG border =\"0\" src='" + tld + "/pict/a.gif'></TH><TH class=\"cga\" onclick=\"trialti();\">Alti.</TH><TH class=\"cgz\">Vz</TH></TR></table>";
  document.getElementById("ac").innerHTML = "<span style=\"color: #333; font-weight: bold; font-size: 1.1em; line-height: 1.3em;\">&nbsp;&nbsp;&nbsp;..::Aircraft::..</span><BR><span class=\"act\">CN: </span><span id=\"accn\" class=\"aca\"></span><BR><DIV id=\"ac1\"><span class=\"act\">Regist.: </span><span id=\"acre\" class=\"aca\"></span><BR></DIV><span class=\"act\">Device Id: </span><span id=\"acfi\" class=\"aca\"></span><BR><span class=\"act\">Type: </span><span id=\"acty\" class=\"aca\"></span><BR><DIV id=\"ac2\"><span class=\"act\">Model: </span><span id=\"acmo\" class=\"aca\"></span></DIV><span class=\"act\">Last time: </span><span id=\"aclt\" class=\"aca\"></span><BR><span class=\"act\">Latitude: </span><span id=\"acla\" class=\"aca\"></span><BR><span class=\"act\">Longitude: </span><span id=\"aclo\" class=\"aca\"></span><BR><span class=\"act\">Altitude: </span><span id=\"acal\" class=\"aca\"></span><BR><span class=\"act\">G.Speed: </span><span id=\"acsp\" class=\"aca\"></span><BR><span class=\"act\">Track: </span><span id=\"actr\" class=\"aca\"></span><span class=\"aca\">&thinsp;&deg;</span><BR><span class=\"act\">Vz: </span><span id=\"acvz\" class=\"aca\"></span><BR><span class=\"act\">Receiver: </span><span id=\"acrx\" class=\"aca\"></span><BR><span id=\"acif\" class=\"aca\"></span>";
  document.getElementById("dtable").innerHTML = "<DIV id=\"menu\" style=\"display:none;\"></DIV><DIV id=\"dtlist\" style=\"display:block\"></DIV>";
//  document.getElementById("menu").innerHTML = "<TABLE class=\"tt\"><TR><TD><INPUT type=\"checkbox\" id=\"hnewbox\" onChange='javascript : hidenew();'> Hide new gliders<BR><INPUT type=\"checkbox\" id=\"offl\" onChange='javascript : lineoff();'" + ((all === 0) ? " checked" : "") + "> Ignore Offline<HR><INPUT type=\"checkbox\" id=\"boundsbox\" onChange='javascript : bounds();'" + ((bound === true) ? " checked" : "") + "> Bounds<BR><TABLE cellspacing=\"0\" cellpading=\"0\"><TR align=\"center\"><TD colspan=\"2\"><INPUT type=\"text\" id=\"latmax\" name=\"latmax\" size=\"7\" value=\"" + amax + "\"></TD></TR><TR align=\"center\"><TD><INPUT type=\"text\" id=\"lonmin\" name=\"lonmin\" size=\"7\" value=\"" + omin + "\"></TD><TD><INPUT type=\"text\" id=\"lonmax\" name=\"lonmax\" size=\"7\" value=\"" + omax + "\"></TD></TR><TR align=\"center\"><TD colspan=\"2\"><INPUT type=\"text\" id=\"latmin\" name=\"latmin\" size=\"7\" value=\"" + amin + "\"></TD></TR></TABLE><BR>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<INPUT type=\"button\" onclick=\"settomap()\" value=\"Set to map\"><BR><INPUT type=\"checkbox\" id=\"astmbox\" onChange='javascript : astm();'> Auto Set to map<HR>..:: Devices ::..<BR><INPUT type=\"checkbox\" id=\"ICAObox\" onChange=\"javascript : devtype();\"> ICAO<BR><INPUT type=\"checkbox\" id=\"Flarmbox\" onChange=\"javascript : devtype();\"> Flarm<BR><INPUT type=\"checkbox\" id=\"OGNbox\" onChange=\"javascript : devtype();\"> OGN Trackers<HR>..:: Layers ::..<BR><INPUT type=\"checkbox\" id=\"tembox\" onChange=\"javascript : tempe();\"> Temperature <BR><INPUT type=\"checkbox\" id=\"winbox\" onChange=\"javascript : wind();\"> Wind <a title=\"openportguide.de\" href=\"http://openportguide.de/index.php/en\" target=\"_blank\"><img src=\"pict/OpenPortGuideLogo_32.png\" style=\"float: right;\" border=\"0\" alt=\"\"></a><BR><INPUT type=\"checkbox\" id=\"prebox\" onChange=\"javascript : pres();\"> Pressure <BR><INPUT type=\"checkbox\" id=\"raibox\" onChange=\"javascript : rain();\"> Precipitation <BR><INPUT type=\"checkbox\" id=\"aspbox\" onChange=\"javascript : asp();\"> AirSpaces <A HREF=\"http://www.openaip.net\" target=\"_blank\" style=\"font-size:10px;\">( openaip.net )</A><BR><INPUT type=\"checkbox\" id=\"aptbox\" onChange=\"javascript : apt();\"> Airports <A HREF=\"http://www.openaip.net\" target=\"_blank\" style=\"font-size:10px;\">( openaip.net )</A><BR><INPUT type=\"checkbox\" id=\"reclbox\" onChange=\"javascript : reclbox();\"> Receivers<BR><span id=\"dtaskbox\"><INPUT type=\"checkbox\" disabled></span> <span onclick=\"taskclic();\">Tasks</span><BR> <DIV style=\"display:none\"><input type=\"file\" id=\"chfile\" onchange=\"rtask()\" /></DIV><HR>..::Units::..<BR><input type=\"radio\" name=\"units\" id=\"unm\" value=\"m\" onclick=\"chunit()\" checked>Met. <input type=\"radio\" name=\"units\" id=\"uni\" value=\"i\" onclick=\"chunit()\">Imp.<HR>..::Path length::..<BR><input type=\"radio\" name=\"pl\" id=\"rp1\" value=\"1\" checked onclick=\"chpl()\">5' <input type=\"radio\" name=\"pl\" id=\"rp2\" value=\"2\" onclick=\"chpl()\">10' <input type=\"radio\" name=\"pl\" id=\"rp3\" value=\"3\" onclick=\"chpl()\">All<HR><CENTER>Join the<BR><A HREF=\"http://ddb.glidernet.org\" target=\"_blank\">OGN DataBase</A></CENTER><HR><CENTER><A HREF=\"https://github.com/glidernet/ogn-live\" target=\"_blank\">Sources</A></CENTER></TD></TR></TABLE>";
//  document.getElementById("menu").innerHTML = "<TABLE class=\"tt\"><TR><TD><INPUT type=\"checkbox\" id=\"hnewbox\" onChange='javascript : hidenew();'> Hide new gliders<BR><INPUT type=\"checkbox\" id=\"offl\" onChange='javascript : lineoff();'" + ((all === 0) ? " checked" : "") + "> Ignore Offline<HR><INPUT type=\"checkbox\" id=\"boundsbox\" onChange='javascript : bounds();'" + ((bound === true) ? " checked" : "") + "> Bounds<BR><TABLE cellspacing=\"0\" cellpading=\"0\"><TR align=\"center\"><TD colspan=\"2\"><INPUT type=\"text\" id=\"latmax\" name=\"latmax\" size=\"7\" value=\"" + amax + "\"></TD></TR><TR align=\"center\"><TD><INPUT type=\"text\" id=\"lonmin\" name=\"lonmin\" size=\"7\" value=\"" + omin + "\"></TD><TD><INPUT type=\"text\" id=\"lonmax\" name=\"lonmax\" size=\"7\" value=\"" + omax + "\"></TD></TR><TR align=\"center\"><TD colspan=\"2\"><INPUT type=\"text\" id=\"latmin\" name=\"latmin\" size=\"7\" value=\"" + amin + "\"></TD></TR></TABLE><BR>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<INPUT type=\"button\" onclick=\"settomap()\" value=\"Set to map\"><BR><INPUT type=\"checkbox\" id=\"astmbox\" onChange='javascript : astm();'> Auto Set to map<HR>..:: Devices ::..<BR><INPUT type=\"checkbox\" id=\"ICAObox\" onChange=\"javascript : devtype();\"> ICAO<BR><INPUT type=\"checkbox\" id=\"Flarmbox\" onChange=\"javascript : devtype();\"> Flarm<BR><INPUT type=\"checkbox\" id=\"OGNbox\" onChange=\"javascript : devtype();\"> OGN Trackers<HR>..:: Layers ::..<BR><INPUT type=\"checkbox\" id=\"tembox\" onChange=\"javascript : tempe();\"> Temperature <BR><INPUT type=\"checkbox\" id=\"winbox\" onChange=\"javascript : wind();\"> Wind <a title=\"openportguide.de\" href=\"http://openportguide.de/index.php/en\" target=\"_blank\"><img src=\"pict/OpenPortGuideLogo_32.png\" style=\"float: right;\" border=\"0\" alt=\"\"></a><BR><INPUT type=\"checkbox\" id=\"prebox\" onChange=\"javascript : pres();\"> Pressure <BR><INPUT type=\"checkbox\" id=\"raibox\" onChange=\"javascript : rain();\"> Precipitation <BR><INPUT type=\"checkbox\" id=\"aspbox\" onChange=\"javascript : asp();\"> AirSpaces <A HREF=\"http://www.openaip.net\" target=\"_blank\" style=\"font-size:10px;\">( openaip.net )</A><BR><INPUT type=\"checkbox\" id=\"aptbox\" onChange=\"javascript : apt();\"> Airports <A HREF=\"http://www.openaip.net\" target=\"_blank\" style=\"font-size:10px;\">( openaip.net )</A><BR><INPUT type=\"checkbox\" id=\"reclbox\" onChange=\"javascript : reclbox();\"> Receivers<BR><span id=\"dtaskbox\"><INPUT type=\"checkbox\" disabled></span> <span onclick=\"taskclic();\">Tasks</span><BR> <DIV style=\"display:none\"><input type=\"file\" id=\"chfile\" onchange=\"rtask()\" /></DIV><HR>..::Units::..<BR><input type=\"radio\" name=\"units\" id=\"unm\" value=\"m\" onclick=\"chunit()\" checked>Met. <input type=\"radio\" name=\"units\" id=\"uni\" value=\"i\" onclick=\"chunit()\">Imp.<HR>..::Path length::..<BR><input type=\"radio\" name=\"pl\" id=\"rp1\" value=\"1\" checked onclick=\"chpl()\">5' <input type=\"radio\" name=\"pl\" id=\"rp2\" value=\"2\" onclick=\"chpl()\">10' <input type=\"radio\" name=\"pl\" id=\"rp3\" value=\"3\" onclick=\"chpl()\">All<HR>..:: Altitude ::..<BR><INPUT type=\"checkbox\" id=\"stick\" onChange=\"javascript : chstick();\"> Altitude stick<HR><CENTER>Join the<BR><A HREF=\"http://ddb.glidernet.org\" target=\"_blank\">OGN DataBase</A></CENTER><HR><CENTER><A HREF=\"https://github.com/glidernet/ogn-live\" target=\"_blank\">Sources</A></CENTER></TD></TR></TABLE>";
  document.getElementById("menu").innerHTML = "<TABLE class=\"tt\"><TR><TD><INPUT type=\"checkbox\" id=\"hnewbox\" onChange='javascript : hidenew();'> Hide new gliders<BR><INPUT type=\"checkbox\" id=\"offl\" onChange='javascript : lineoff();'" + ((all === 0) ? " checked" : "") + "> Ignore Offline"+
	  "<HR><INPUT type=\"checkbox\" id=\"boundsbox\" onChange='javascript : bounds();'" + ((bound === true) ? " checked" : "") + "> Bounds<BR><TABLE cellspacing=\"0\" cellpading=\"0\"><TR align=\"center\"><TD colspan=\"2\"><INPUT type=\"text\" id=\"latmax\" name=\"latmax\" size=\"7\" value=\"" + amax + "\"></TD></TR><TR align=\"center\"><TD><INPUT type=\"text\" id=\"lonmin\" name=\"lonmin\" size=\"7\" value=\"" + omin + "\"></TD><TD><INPUT type=\"text\" id=\"lonmax\" name=\"lonmax\" size=\"7\" value=\"" + omax + "\"></TD></TR><TR align=\"center\"><TD colspan=\"2\"><INPUT type=\"text\" id=\"latmin\" name=\"latmin\" size=\"7\" value=\"" + amin + "\"></TD></TR></TABLE><BR>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<INPUT type=\"button\" onclick=\"settomap()\" value=\"Set to map\"><BR><INPUT type=\"checkbox\" id=\"astmbox\" onChange='javascript : astm();'> Auto Set to map"+
	  "<HR>..:: Devices ::..<BR><INPUT type=\"checkbox\" id=\"ICAObox\" onChange=\"javascript : devtype();\"> ICAO<BR><INPUT type=\"checkbox\" id=\"Flarmbox\" onChange=\"javascript : devtype();\"> Flarm<BR><INPUT type=\"checkbox\" id=\"OGNbox\" onChange=\"javascript : devtype();\"> OGN Trackers"+
	  "<HR>..:: Layers ::..<BR><INPUT type=\"checkbox\" id=\"tembox\" onChange=\"javascript : tempe();\"> Temperature <BR><INPUT type=\"checkbox\" id=\"winbox\" onChange=\"javascript : wind();\"> Wind <a title=\"openportguide.de\" href=\"http://openportguide.de/index.php/en\" target=\"_blank\"><img src=\"pict/OpenPortGuideLogo_32.png\" style=\"float: right;\" border=\"0\" alt=\"\"></a><BR><INPUT type=\"checkbox\" id=\"prebox\" onChange=\"javascript : pres();\"> Pressure <BR><INPUT type=\"checkbox\" id=\"raibox\" onChange=\"javascript : rain();\"> Precipitation <BR><INPUT type=\"checkbox\" id=\"aspbox\" onChange=\"javascript : asp();\"> AirSpaces <A HREF=\"http://www.openaip.net\" target=\"_blank\" style=\"font-size:10px;\">( openaip.net )</A><BR><INPUT type=\"checkbox\" id=\"aptbox\" onChange=\"javascript : apt();\"> Airports <A HREF=\"http://www.openaip.net\" target=\"_blank\" style=\"font-size:10px;\">( openaip.net )</A><BR><INPUT type=\"checkbox\" id=\"reclbox\" onChange=\"javascript : reclbox();\"> Receivers<BR><span id=\"dtaskbox\"><INPUT type=\"checkbox\" disabled></span> <span onclick=\"taskclic();\">Tasks</span><BR> <DIV style=\"display:none\"><input type=\"file\" id=\"chfile\" onchange=\"rtask()\" /></DIV>"+
	  "<HR>..::Units::..<BR><input type=\"radio\" name=\"units\" id=\"unm\" value=\"m\" onclick=\"chunit()\" checked>Met. <input type=\"radio\" name=\"units\" id=\"uni\" value=\"i\" onclick=\"chunit()\">Imp."+
	  "<HR>..::Path length::..<BR><input type=\"radio\" name=\"pl\" id=\"rp1\" value=\"1\" checked onclick=\"chpl()\">5' <input type=\"radio\" name=\"pl\" id=\"rp2\" value=\"2\" onclick=\"chpl()\">10' <input type=\"radio\" name=\"pl\" id=\"rp3\" value=\"3\" onclick=\"chpl()\">All"+
	  "<HR>..:: Altitude ::..<BR><INPUT type=\"checkbox\" id=\"stick\" onChange=\"javascript : chstick();\"> Altitude stick<BR><INPUT type=\"checkbox\" id=\"baro\" onChange=\"javascript : chbaro();\"> Barogram"+
	  "<HR><CENTER>Join the<BR><A HREF=\"http://ddb.glidernet.org\" target=\"_blank\">OGN DataBase</A></CENTER><HR><CENTER><A HREF=\"https://github.com/glidernet/ogn-live\" target=\"_blank\">Sources</A></CENTER></TD></TR></TABLE>";

  // parameter b=lat1,lon1,lat2,lon2 bounds
  if (typeof(parh.b) != 'undefined') {
    cent = parh.b.split(',');
    document.getElementById('latmax').value = parseFloat(cent[0]);
    document.getElementById('latmin').value = parseFloat(cent[1]);
    document.getElementById('lonmax').value = parseFloat(cent[2]);
    document.getElementById('lonmin').value = parseFloat(cent[3]);
    boundc = "&b=" + cent[0] + "&c=" + cent[1] + "&d=" + cent[2] + "&e=" + cent[3];
    document.getElementById('boundsbox').checked = true;
    bound = true;
    hashb = "&b=" + cent[0] + "," + cent[1] + "," + cent[2] + "," + cent[3];
  }
	else {
		// force auto set to map to avoid problem when there is too much aircrafts
		document.getElementById('astmbox').checked = true;
    vstm = true;
    hashs = "&s=1";
	}

  // parameter l= active layers
  if (typeof(parh.l) != 'undefined') {
    for (var i = 0; i < parh.l.length; i++) {
      switch (parh.l[i]) {
        case 't': // temperature
          document.getElementById('tembox').checked = true;
          tempe();
          break;				
        case 'v': // wind
          document.getElementById('winbox').checked = true;
          wind();
          break;
        case 'p': // pressure
          document.getElementById('prebox').checked = true;
          pres();
          break;
        case 'n': // precipitation
          document.getElementById('raibox').checked = true;
          rain();
          break;					
        case 'z': // airspace
          document.getElementById('aspbox').checked = true;
          asp();
          break;
        case 'a': // airport
          document.getElementById('aptbox').checked = true;
          apt();
          break;
        case 'r': // receivers
          document.getElementById('reclbox').checked = true;
          break;
      }
    }
  }

  if (typeof(parh.t) != 'undefined') {
    gmdelay = 1;
    var xhr = new XMLHttpRequest();
    xhr.open("GET", parh.t, true);
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4) {
        var status = xhr.status;
        if ((status >= 200 && status < 300) || status === 304) {
          loadtask(xhr.responseText);
        } else {
          alert("Task Request unsuccessful" + status);
        }
      }
      gesmark();
    };

    xhr.send(null);
  }

  // parameter w=0 (Don't display the warning)
  var warn = 1;
  if (typeof(parh.w) != 'undefined') {
    if (parh.w == "0") {
      warn = 0;
      hashw = "&w=0";
    }
  }

  // parameter n=0 (Hide the panel)
  if (typeof(parh.n) != 'undefined') {
    if (parh.n == "0") {
      alist();
    }
  }

  if (warn == 1) {
    document.getElementById("popup").innerHTML = "<img class=\"pr\" alt=\"close\" src=\"" + tld + "/pict/close.png\"><H1>Warning!</H1><BR><P style=\"text-align:justify;\"><B>The data on this site can be ambiguous in certain situations and the displayed position of an aircraft or glider can be displaced relative to the actual position.<BR>Before raising an alert please contact us so we can interpret the data correctly.</B><BR><BR><B>If you want your devices to be identified, join the <A HREF=\"http://ddb.glidernet.org\" target=\"_blank\">OGN DataBase</A>.</B></P>";
    op(300);
  }

  /*
	// parameter s=1 auto set bounds to the map
  if (typeof(parh.s) != 'undefined') {
    if (parh.s == "1") {
		  document.getElementById('astmbox').checked = true;
      vstm = true;
      hashs = "&s=1";
    }
  }
	*/

  // parameter u=i units imperial ou metric (default))
  if (typeof(parh.u) != 'undefined') {
    if (parh.u == "i") {
      document.getElementById('uni').checked = true;
      unit = "i";
      hashu = "&u=i";
			scaleLineControl.setUnits(unitlist[unit]);
    }
  }

  // parameter a=0 (Display an altitude stick)
  if (typeof(parh.a) != 'undefined') {
    if (parh.a == "1") {
      document.getElementById('stick').checked = true;
      stick = 1;
      hasha = "&a=1";
			sticksLayer.setVisible(true);
    }
  }

  // parameter g=0 (Display a barogram)
  if (typeof(parh.g) != 'undefined') {
    if (parh.g == "1") {
      document.getElementById('baro').checked = true;
      document.getElementById('dbaro').style.display = "block";
			document.getElementById('dbaro').style.visibility = "visible";
      barogram = 1;
      hashg = "&g=1";
    }
  }

  // parameter p=1,2 or 3 path length 5", 10" or all points
  if (typeof(parh.p) != 'undefined') {
    if (parh.p == "2") { // 10 minutes
      pathl = 60;
      document.getElementById('rp2').checked = true;
      hashp = "&p=2";
    } else if (parh.p == "3") { // all points
      pathl = 99999;
      document.getElementById('rp3').checked = true;
      hashp = "&p=3";
    }
    baro_reSize();
  }

  // parameter device type d=1 ICAO ,2 Flarm or 3 OGN tracker
  if (typeof(parh.y) != 'undefined') {
    if ((parh.y & 1) == 1) {
      document.getElementById('ICAObox').checked = true;
    }
    if ((parh.y & 2) == 2) {
      document.getElementById('Flarmbox').checked = true;
    }
    if ((parh.y & 4) == 4) {
      document.getElementById('OGNbox').checked = true;
    }
    devtype();
  } else {
    document.getElementById('ICAObox').checked = true;
    document.getElementById('Flarmbox').checked = true;
    document.getElementById('OGNbox').checked = true;
  }



  tz = "&z=" + (tz / -60); // the javascript gettimezone function return negative value in minutes then /-60 to have correct hours

  rehash();
  checkrec();
	

	const body = document.querySelector('body');
	body.onkeydown = function(e) {
		if (e.keyCode == 9) {
			if (document.getElementById('latmin')===document.activeElement || document.getElementById('latmax')===document.activeElement || document.getElementById('lonmin')===document.activeElement || document.getElementById('lonmax')===document.activeElement)  {
				// nothing
			} else {	// swap menu
				e.preventDefault();
				onofff();
			}
		}
		
	};
	
	
  tmwd = setTimeout(wd, 30000);
  if (gmdelay == 0) gesmark();

  // barogram plotting
  baro_Init();
}