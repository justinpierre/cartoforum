var map;

function showAcctDiv() {
$( "#createAccount" ).show( "fast" );
}

function showPwDiv() {
$( "#forgotPassword" ).show( "fast" );
}

function makeNewGroup() {
$( "#newGroup" ).show( "fast" );
if (!map) init();
}

function invite(x) {
x.innerhtml = "<input class = 'inviteuserid' name = 'userid'>";
}

function init() {
  var base = new ol.layer.Tile({
	visible: true,
	source: new ol.source.OSM()
  });

  map = new ol.Map({
	layers: [base],
	renderer: 'canvas',
	target: 'map',
	view: new ol.View({
		center: [0,0],
		zoom: 1
	})
  });
  map.on('moveend', onMoveEnd);



}

function onMoveEnd(evt) {
  var map = evt.map;
  var extent = map.getView().calculateExtent(map.getSize());
  var bottomLeft = ol.extent.getBottomLeft(extent);
  var topRight = ol.extent.getTopRight(extent);
  var bounds = bottomLeft[0] + " " + bottomLeft[1] + " " + topRight[0] + " " + topRight[1];
  document.getElementById("bounds").value = bounds;
  
}

function wrapLon(value) {
  var worlds = Math.floor((value + 180) / 360);
  return value - (worlds * 360);
}

function addGeojson(groupid) {
  var addgeojsonform = '<p id = "closegeojsonwindow" onclick = "$( \'#addgeojson\' ).hide(\'fast\')">x</p>';
  addgeojsonform += "<form method = 'POST' id = 'geojsonform' action = '#'>";
  addgeojsonform += "<br>";
  addgeojsonform += "<textarea rows = '15' cols = '70' name='geojson' id = 'geojson'></textarea>";
  addgeojsonform += "<input type = 'button' value = 'save' class = 'btn bbtn' onclick = 'geojsonSubmit(" + groupid + ")'>"; 
  $( "#addgeojson" ).html(addgeojsonform);
  $( "#addgeojson" ).show("fast");
}

function geojsonSubmit(groupid) {
   var geojsondata = JSON.parse($( "#geojson" ).val());

   for (var i in geojsondata.features) {
   var vsource = new ol.source.GeoJSON(
    /** @type {olx.source.GeoJSONOptions} */ ({
      object: {
        'type': 'FeatureCollection',
        'crs': {
          'type': 'name',
          'properties': {
            'name': 'EPSG:4326'
          }
        },
        'features': JSON.parse("["+JSON.stringify(geojsondata.features[i])+"]")
       }
  }));


  var format = new ol.format['WKT']();
  var data = format.writeFeatures(vsource.getFeatures());
  var ajaxRequest = new XMLHttpRequest();
  var querystring = "geojson="+encodeURIComponent(data)+"&groupid="+groupid;
  ajaxRequest.open("POST", "serverops/addGeoJSON.php", true);
  ajaxRequest.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  ajaxRequest.send(querystring);
 }
   $( '#addgeojson' ).hide('fast');
}

function removeUser(userid, username, groupid) {
if (confirm("Delete user " + username + "?")) {
  $( "#removeUserValue" ).val(userid);
  $( "#removeFromGroup" ).val(groupid);
  $( "#removeUser" ).submit();
 }
}

function retireThread(threadid, groupid,status) {
if (confirm("For sure?")) {
  $( "#threadid" ).val(threadid);
  $( "#threadGroup" ).val(groupid);
  $( "#threadstatus" ).val(status);
  $( "#retireThread" ).submit();

 }
}

function deleteGroup() {
  var r = confirm("Are you sure you want to delete this group and all of the content?");
if (r == true) {
      $( "#deletegroupform" ).submit();
} else {
    return;
}


}

function getUserGroups() {
    $.getJSON($SCRIPT_ROOT + '/_get_user_groups',
    function(data) {
        console.log(data.groups);
        for (var i=0; i < data.groups.length; i++) {
            $("#description").append("<p>"+data.groups[i]['name']+"</p>");
        }
    }
    )
 }

