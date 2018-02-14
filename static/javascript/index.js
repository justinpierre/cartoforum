var map;

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
        if (data.groups.length == 0) {
            $("#description").append("You don't belong to any groups yet.<br><br>");
            $("#description").append("check out the ");
            $("#description").append("<input type = 'button' value = 'Discovery Map' onclick = 'goToDisc()'");
            $("#description").append(" for some inspiration");
        }
        else {
            $("#description").append("<table>");
            for (var i=0; i < data.groups.length; i++) {
                var newrow = $("<tr></tr>");
                var newcell = $("<td></td>");
                var groupForm = $("<form method = 'POST' action = '/map'></form>");
                groupForm.append('<input type = "hidden" name = "groupid" value = "' + data.groups[i]['groupid'] + '">');
                groupForm.append('<input type = "submit" class = "bbtn btn" value = "' + data.groups[i]['name'] + '">');
                newcell.append(groupForm);
                newrow.append(newcell);
                if (data.groups[i]['admin'] == "true") {
                    var newcell = $("<td></td>");
                    var adminForm = $("<form method = 'POST' action = '/admin'></form>");
                    adminForm.append('<input type = "hidden" name = "groupid" value = "'+ data.groups[i]['groupid'] + '">');
                    adminForm.append('<input type = "submit" class = "bbtn btn" value = "admin">');
                    newcell.append(adminForm);
                    newrow.append(newcell);
                }
                else {
                    newrow.append('<td></td>')
                }
                $("#description").append(newrow);
            }
            $("#description").append("</table>");
        }
    })
    getUserInvites();
 }

 function getGroupUsers() {
     $.getJSON($SCRIPT_ROOT + '/_get_group_users',
     function(data){
     for (var i =0; i<data.users.length; i++) {
         $("#users").append("<tr><td>" + data.users[i]['name'] + "</td></tr>");
        }}
      )
 }


function getUserInvites() {
    $.getJSON($SCRIPT_ROOT + '/_get_user_invites',
    function(data) {
        for (var i=0; i < data.invites['invites'].length; i++) {
            var inviteForm = $("<form method = 'POST' action = '/manageInvite'></form>")
            inviteForm.append(data.invites['invites'][i]['requester'] + " has invited you to the group " + data.invites['invites'][i]['group']);
            inviteForm.append('<input type = "hidden" name = "requestid" value = "' + data.invites['invites'][i]['requestid'] + '" />');
            inviteForm.append('<input type = "submit" name = "submit" value = "accept" class= "btn bbtn"/>');
            inviteForm.append('<input type = "submit" name = "submit" value = "reject" class= "btn wbtn"/>');
            $("#invites").append(inviteForm);
        }
        for (var i=0; i < data.invites['requests'].length; i++) {
            var inviteForm = $("<form method = 'POST' action = '/manageRequest'></form>")
            inviteForm.append(data.invites['requests'][i]['requester'] + "has requested a membership to the group " + data.invites['requests'][i]['group']);
            inviteForm.append('<input type = "hidden" name = "requestid" value = "' + data.invites['requests'][i]['requestid'] + '" />');
            inviteForm.append('<input type = "submit" name = "submit" value = "accept" class= "btn bbtn"/>');
            inviteForm.append('<input type = "submit" name = "submit" value = "reject" class= "btn wbtn"/>');
            $("#invites").append(inviteForm);
        }
    })
}


function groupCreate() {
    $.ajax({
        url: $SCRIPT_ROOT + '/createGroup',
        type: 'POST',
        contentType: 'application/json;charset=UTF-8',
        cache: false,
        data: JSON.stringify({'groupname': $("#groupName").val(), 'opengroup': $("#opengroup").val(), 'bounds': $("#bounds").val()}),
        success: function (response) {
            $("#description").html()
            $( "#newGroup" ).hide( "fast" );
            getUserGroups();

        }

    })
}

function getThreads() {
 $.getJSON($SCRIPT_ROOT + '/_get_group_threads',
    {groupid: groupid},
    function(data) {
      $("#threads").append()
    }
)
 getGroupUsers();
}