var map, typeSelect, draw, vector, groupobjectssrc, groupobjects, overlay, container, content, closer, selectedObjectSrc, selectedobject, selectExisting, digitizing, modify, select, threadsrc,light,dark;
var replyID = null;

var postHTML = '<textarea id = "new-objinfo" placeholder = "Write your post here and select an option below"></textarea>';
postHTML += '<br>';
postHTML += '<label>Create a:</label>';
postHTML += '<select id="type">';
postHTML += '<option value="null" selected="selected"></option>';
postHTML += '<option value="Point">Point</option>';
postHTML += '<option value="LineString">Line</option>';
postHTML += '<option value="Polygon">Polygon</option>';
postHTML += '<option value="None" >None</option>';
postHTML += '<option value="Select From Map">Select From Map</option>';
postHTML += '<option value="Edit">Edit</option>';
postHTML += '</select>';
postHTML += '<input type = "button" value = "save" class = "bbtn" onclick = "saveObject()">';


var style = new ol.style.Style({
    fill: new ol.style.Fill({
      color: 'rgba(255, 255, 255, 0.2)'
    }),
    stroke: new ol.style.Stroke({
      color: '#ffcc33',
      width: 2
    }),
    image: new ol.style.Circle({
      radius: 7,
      fill: new ol.style.Fill({
        color: '#ffcc33'
      })
    })
  });

var selectstyle = new ol.style.Style({
    fill: new ol.style.Fill({
      color: 'rgba(255, 255, 0, 0.2)'
    }),
    stroke: new ol.style.Stroke({
      color: '#ffff00',
      width: 2
    }),
    image: new ol.style.Circle({
      radius: 7,
      fill: new ol.style.Fill({
        color: '#ffff00'
      })
    })
  });

var vsource = new ol.source.Vector({
  features: []
});

function init() {
  content = document.getElementById('popup-content');
  base = new ol.layer.Tile({
	visible: true,
	source: new ol.source.OSM()
});


 light = new ol.layer.Tile({
      source: new ol.source.XYZ({url: 'http://s.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'}),
      sphericalMercator: true,
      attributions: [new ol.Attribution({ html: ['&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>'] })]
    });

dark = new ol.layer.Tile({
      visible:false,
      source: new ol.source.XYZ({url: 'http://s.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'}),
      sphericalMercator: true,
      attributions: [new ol.Attribution({ html: ['&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>'] })]
    });

   aerial = new ol.layer.Tile({
    visible: false,
    preload: Infinity,
    source: new ol.source.BingMaps({
      key: 'AisImhS1UITy73JDKW7Uelqw_vYcFBnzD-01HGU_LZc9A75jvgp1aBOLtgRo3O3m',
      imagerySet: 'Aerial'
    })
  });

groupobjectssrc = new ol.source.TileWMS(/** @type {olx.source.TileWMSOptions} */ ({
url: 'http://cartoforum.com:8080/geoserver/wms',
                params: {'LAYERS': 'Argoomap_postgis:groupobjects', 'TRANSPARENT': true, 'TILED': false, 'viewparams': 'groupid:'+groupid},
		serverType: 'geoserver'
	     }));if (style == 1) dark.setVisible(1);

  groupobjects = new ol.layer.Tile({source: groupobjectssrc, visible: true});

vector = new ol.layer.Vector({
  style: style,
  source: vsource
});

/*
vector.on('change', function(e) {
  var format = new ol.format['WKT']();
  var data = format.writeFeatures(vector.getSource().getFeatures());
  $( "#geoCollection" ).html(data);
})
*/
map = new ol.Map({
	layers: [light,dark,base, aerial, groupobjects, vector],
	renderer: 'canvas',
	target: 'map',
	view: new ol.View({
		center: [-10000000,6500000],
		zoom: 5
	})
});

  var bounds_array = bounds.split(" ");

  map.getView().fit([parseFloat(bounds_array[0]), parseFloat(bounds_array[1]), parseFloat(bounds_array[2]), parseFloat(bounds_array[3])], map.getSize());

/*wms get feature info*/
map.on('singleclick', function(e) {
  if (digitizing && !selectExisting) return;
  if (selectedObjectSrc) {
	selectedobject.setSource();
	$(".clickedPostTopBar").addClass("postTopBar");
	$(".clickedPostTopBar").removeClass("clickedPostTopBar");
	}
  var viewResolution = /** @type {number} */ (map.getView().getResolution());
  var url = groupobjectssrc.getGetFeatureInfoUrl( e.coordinate, viewResolution, 'EPSG:3857', {'INFO_FORMAT': 'text/html'});
  url = "http://127.0.0.1" + url.substring(21);
  url="serverops/proxy1.php?url="+encodeURIComponent(url);

  var xmlhttp = new XMLHttpRequest();
  xmlhttp.onreadystatechange=function() {
	  if (xmlhttp.readyState==4 && xmlhttp.status==200) {
	    var xmlDoc = xmlhttp.responseText;
	    if (xmlDoc.search("class")!=-1 && xmlDoc.search("No QUERY_LAYERS has been requested, or no queriable layer in the request anyways")==-1 && xmlDoc) {
	      content.innerHTML = xmlDoc;
              $( "#objinfo" ).show( "fast" );
	      var x = content.getElementsByTagName("td");
	      if (selectExisting) selectExisting = x[1].innerHTML;
	      else $( "#objid" ).html(x[1].innerHTML);
              highlightObject(null, x[1].innerHTML);
	     }
	   }
        }
        xmlhttp.open("GET",url);
        xmlhttp.send();

 });

//basedata toggle
$('#layer-select').change(function() {
  var style = $(this).find(':selected').index();
	aerial.setVisible(0);
	base.setVisible(0);
	dark.setVisible(0);
	base.setVisible(0);
if (style == 0) light.setVisible(1);
if (style == 1) dark.setVisible(1);
if (style == 2) aerial.setVisible(1);
if (style == 3) base.setVisible(1);
});
$('#layer-select').trigger('change');

//filter posts by thread
$('#filter-by-thread').change(function() {
 $( '#createThread' ).html( '' );
  var threadid = $(this).find(':selected').val();
  if (threadid == "new") newThread();
  else if (threadid != "none") {
     var ajaxRequest = new XMLHttpRequest();
     ajaxRequest.onreadystatechange=function() {
     if (ajaxRequest.readyState==4 && ajaxRequest.status==200) {
       var responsedata = ajaxRequest.responseText;
       $( "#objid" ).html(responsedata);
     }
     }
     ajaxRequest.open("GET", "serverops/threads.php?threadid="+threadid, true);
     ajaxRequest.send(); 
     threadsrc = new ol.source.TileWMS(/** @type {olx.source.TileWMSOptions} */ ({
     url: 'http://cartoforum.com:8080/geoserver/wms',
                params: {'LAYERS': 'Argoomap_postgis:threadview', 'TRANSPARENT': true, 'TILED': false, 'viewparams': 'groupid:'+groupid+';threadid:'+threadid},
		serverType: 'geoserver'
	     }));
    groupobjects.setSource(threadsrc);
  }
  else groupobjects.setSource(groupobjectssrc);
});
$('#filter-by-thread').trigger('change');

//filter posts by user
$('#filter-by-user').change(function() {
 var userfilter = $(this).find(':selected').val();
 if (userfilter != "none") {
 $( '#createThread' ).html( '' );
  var userid = $(this).find(':selected').val();
   var ajaxRequest = new XMLHttpRequest();
   ajaxRequest.onreadystatechange=function() {
   if (ajaxRequest.readyState==4 && ajaxRequest.status==200) {
     var responsedata = ajaxRequest.responseText;
     $( "#objid" ).html(responsedata);
   }
   }
   ajaxRequest.open("GET", "serverops/userPosts.php?userid="+userid+"&groupid="+groupid, true);
   ajaxRequest.send(); 
  }});
$('#filter-by-user').trigger('change');

/* var serverPoll = setInterval(function() {
 var ajaxRequest = new XMLHttpRequest();
 ajaxRequest.onreadystatechange=function() {
 if (ajaxRequest.readyState==4 && ajaxRequest.status==200) {
   var responsedata = ajaxRequest.responseText;
   if (responsedata != instanceid) {
	var params = groupobjectssrc.getParams();
	  params.t = new Date().getMilliseconds();
	  groupobjectssrc.updateParams(params);
	 instanceid = responsedata;
   }
  }
 }
 ajaxRequest.open("GET", "serverops/checkInstance.php?g="+groupid, true);
 ajaxRequest.send();
}, 10000);

$('.sidebar').jScrollPane();
*/
recentPosts();
}

//style toggle
function styleChange(color) {
  $("#selectedStyle").attr("src","images/"+color+".gif");
  groupobjectssrc.updateParams({STYLES: color});
  if (threadsrc) threadsrc.updateParams({STYLES: color});
  $( 'div#style-select-options' ).hide('fast');
}

function addInteraction() {
  digitizing = true;
  var value = typeSelect.options[typeSelect.selectedIndex].value;
  draw = new ol.interaction.Draw({
      source: vsource,
      type: /** @type {ol.geom.GeometryType} */ (value)
    });
 

  if (typeSelect.options[typeSelect.selectedIndex].index<4) {
    map.addInteraction(draw);
  }
  else if (value == 'Select From Map') {
    groupobjects.setSource(groupobjectssrc);
    selectExisting = true;
  }
  else if (value == 'Edit') {
      select = new ol.interaction.Select({style: selectstyle});
      map.addInteraction(select);
      modify = new ol.interaction.Modify({
        features: select.getFeatures()
      });
   map.addInteraction(modify);
 }
  else {
    selectExisting = false;
    groupobjects.setSource(threadsrc);
  }
}

function recentPosts() {
stopDigitizing();
 $( '#createThread' ).html( '' );

$.getJSON($SCRIPT_ROOT + '/_recent_posts', {
        groupid: groupid
        }, function (response) {
            for (var i = 0; i<=response.posts.length;i++) {
                var newpost = "<div class = 'postContent' id = '" + response.posts[i][0] + "' onClick = 'highlightOject(this.id, " + response.posts[i][3] + ")'></div>";
                newpost += "<div class = 'postTopBar'><p class = 'fromfind'>From: " + response.posts[i][5] + "<span style = 'float: right;'><input type = 'button' class = 'btn findbtn' value = '&#x1f50d;' onclick = 'zoomTo(" + response.posts[i][3] + ")'></span></p></div>";
                newpost += "<div class = 'postText'>" + response.posts[i][4] + "</div>";
                $("#posts").append(newpost);
            }

        });

   $( '#filter-by-user' ).val("none");
   $( '#filter-by-thread' ).val("none");
  groupobjects.setSource(groupobjectssrc);
   var params = groupobjectssrc.getParams();
	  params.t = new Date().getMilliseconds();
	  groupobjectssrc.updateParams(params);
}

function postExtent() { 
  var extent = map.getView().calculateExtent(map.getSize());
  var bottomLeft = ol.extent.getBottomLeft(extent);
  var topRight = ol.extent.getTopRight(extent);
  var bounds = bottomLeft[0] + " " + bottomLeft[1] + " " + topRight[0] + " " + topRight[1];

 $( '#createThread' ).html( '' );
 var ajaxRequest = new XMLHttpRequest();
   ajaxRequest.onreadystatechange=function() {
   if (ajaxRequest.readyState==4 && ajaxRequest.status==200) {
     var responsedata = ajaxRequest.responseText;
     $( "#objid" ).html(responsedata);
   }
   }
   ajaxRequest.open("GET", "serverops/postExtent.php?groupid="+groupid+"&b="+bounds, true);
   ajaxRequest.send(); 
   $( '#filter-by-user' ).val("none");
   $( '#filter-by-thread' ).val("none");
  groupobjects.setSource(groupobjectssrc);
}

function searchPosts() {
 var searchstring = $( "#searchPosts" ).val();
 if (searchstring=="") return;
 $( '#createThread' ).html( '' );
 var ajaxRequest = new XMLHttpRequest();
   ajaxRequest.onreadystatechange=function() {
   if (ajaxRequest.readyState==4 && ajaxRequest.status==200) {
     var responsedata = ajaxRequest.responseText;
     $( "#objid" ).html(responsedata);
   }
   }
   ajaxRequest.open("GET", "serverops/searchPosts.php?groupid="+groupid+"&q="+searchstring, true);
   ajaxRequest.send(); 
   $( '#filter-by-user' ).val("none");
   $( '#filter-by-thread' ).val("none");
  groupobjects.setSource(groupobjectssrc);
}

function saveThread() {
  //Save thread
	var ajaxThreadRequest = new XMLHttpRequest();var params = groupobjectssrc.getParams();
	  params.t = new Date().getMilliseconds();
	  groupobjectssrc.updateParams(params);
	var threadString = "?nick="+encodeURIComponent($( "input#new-threadnick" ).val())+"&name="+encodeURIComponent($( "textarea#new-threadname" ).val())+"&g="+groupid;
	ajaxThreadRequest.onreadystatechange=function() {
          if (ajaxThreadRequest.readyState==4 && ajaxThreadRequest.status==200) {
	    location.reload();
          }
         }
        ajaxThreadRequest.open("GET", "serverops/storeThread.php"+threadString, true);
        ajaxThreadRequest.send();
}

function savePost(objid) {
  
  var text_data = $( "textarea#new-objinfo" ).val();
  var ajaxRequestText = new XMLHttpRequest();
  var querystring = "?text="+encodeURIComponent(text_data)+"&g="+groupid+"&u="+userid+"&objid="+objid;
  if (replyID) querystring += "&r="+replyID;
  else { var threadid = document.getElementById("postToThreadID").value;
         querystring +="&t="+ threadid;
  }
  ajaxRequestText.onreadystatechange=function() {
   if (ajaxRequestText.readyState==4 && ajaxRequestText.status==200) {
      replyID = null;
      selectExisting=false;
      $( "div#reply-to-post"+replyID ).html("");
      $( "#objid" ).html("");
      $( "#createThread" ).hide("fast");
      $( "#createThread" ).html("");
      //refresh map
      var params = groupobjectssrc.getParams();
      params.t = new Date().getMilliseconds();
      groupobjectssrc.updateParams(params);
      typeSelect.selectedIndex=0;
      map.removeInteraction(draw);
      map.removeInteraction(modify);  
      map.removeInteraction(select);
      digitizing = false;
   }
  }
  ajaxRequestText.open("GET", "serverops/storeText.php"+querystring, true);
  ajaxRequestText.send();
  recentPosts();
}

function saveObject() {
  typeSelect = document.getElementById('type');
  if (typeSelect.options[typeSelect.selectedIndex].index==0) {
	alert ("Choose a geography type, or if your post doesn't have geography choose none");
        return;
   }
var format = new ol.format['WKT']();
  var data = format.writeFeatures(vector.getSource().getFeatures());  
if (data == "GEOMETRYCOLLECTION EMPTY" && typeSelect.options[typeSelect.selectedIndex].index<4) {
	alert ("It looks like you haven't finished adding any geography. You may need to double click to finish drawing a line or polygon.");
        return;
}
  
  var ajaxRequest = new XMLHttpRequest();
  if (selectExisting >0) savePost(selectExisting);
  else if (data == "GEOMETRYCOLLECTION EMPTY") savePost(null);
  else {
  var querystring = "?obj="+encodeURIComponent(data)+"&g="+groupid+"&u="+userid;
  vsource.clear();
  ajaxRequest.onreadystatechange=function() {
  if (ajaxRequest.readyState==4 && ajaxRequest.status==200) {
    var responsedata = ajaxRequest.responseText;
    var objid=responsedata;
    savePost(objid);
  }
  }
  ajaxRequest.open("GET", "serverops/storeObject.php"+querystring, true);
  ajaxRequest.send();
}
}

function highlightObject(postid, objid) {
    if (selectedObjectSrc) selectedobject.setSource();
    if (objid) {
      selectedObjectSrc = new ol.source.TileWMS(/** @type {olx.source.TileWMSOptions} */ ({
      url: 'http://cartoforum.com:8080/geoserver/wms',
                params: {'LAYERS': 'Argoomap_postgis:SelectedFeatures', 'TRANSPARENT': true, 'TILED': false, 'viewparams': 'objid:'+objid},
		serverType: 'geoserver'
	     }));
      selectedobject = new ol.layer.Tile({source: selectedObjectSrc, visible: true});
      map.addLayer(selectedobject);
    }
 var ajaxRequest = new XMLHttpRequest();
 ajaxRequest.onreadystatechange=function() {
 if (ajaxRequest.readyState==4 && ajaxRequest.status==200) {
   var responsedata = ajaxRequest.responseText;
   $(".clickedPostTopBar").addClass("postTopBar");
    $(".clickedPostTopBar").removeClass("clickedPostTopBar");
     if (!selectExisting) $( "#objid" ).html(responsedata);
     if (!postid) {
      $('#sidebar').animate({
        scrollTop: $(".clickedPostTopBar").offset().top-140
        }, 2000);
  }}
 }
 if (!postid) ajaxRequest.open("GET", "serverops/getPost.php?id="+objid+"&type=objid", true);
 else ajaxRequest.open("GET", "serverops/getPost.php?id="+postid+"&type=postid", true);
 ajaxRequest.send();        
}

function newThread() {
  $( "#objid" ).html("");
  var html = '<div id = "createThread" class = "replyArea"><input type = "text" id = "new-threadnick" placeholder = "Nickname for Thread" /><br>';
  html += '<textarea id = "new-threadname" placeholder = "Thread description"></textarea><br><br>';
  html += '<input type = "button" value = "save" class = "btn bbtn" onclick = "saveThread()">';
  html += '<input type = "button" value = "cancel" class = "btn bbtn" onclick = "$( `#createThread` ).html(``)"></div>';
  $( "#objid" ).html(html);
  $( "#createThread" ).show("fast");


}


function postToThread(threadid) {
   if (!threadid) {
    alert ("Choose a thread");
    return;
  }
  if ($('#filter-by-thread').val(threadid).attr('class') == 'retired') {
    alert("This thread is retired. No further posts accepted");
    return;

  }

$( ".addpost").on({
 "mouseover" : function() {
    this.src = 'images/addhover.png';
  },
  "mouseout" : function() {
    this.src='images/add.png';
  }
});
$(".postToThread").css("display", "none");


var addpostbuttons = document.getElementsByClassName("addpost");
for (var i = 0; i<addpostbuttons.length; i++)   $( "#addtothread"+addpostbuttons[i].id).attr("onclick","postToThread("+addpostbuttons[i].id+")"); 

$( "#addtothread"+threadid).on({
 "mouseover" : function() {
    this.src = 'images/cancelhover.png';
  },
  "mouseout" : function() {
    this.src='images/cancel.png';
  }
});
  $( "#addtothread"+threadid).attr("onclick","stopDigitizing("+threadid+")");
  $( "#filter-by-thread").val(threadid);
  postHTML += '<input type = "hidden" id = "postToThreadID" value = "' +threadid+ '" >';
  $( "#postToThread"+threadid ).html(postHTML);
  $( "#postToThread"+threadid ).show("fast");
  var format = new ol.format['WKT']();
  var data = format.writeFeatures(vector.getSource().getFeatures());
  typeSelect = document.getElementById('type');
  if (selectedobject) selectedobject.setSource();
  typeSelect.onchange = function(e) {
	map.removeInteraction(draw);
	addInteraction();
  }
}

function replyToPost(objid) {
  replyID=objid;
  var html = "<input type = 'hidden' name = 'objid' value = '";
  html += objid;
  html += "' />";   
  html += postHTML;
  $( "div#reply-to-post"+replyID ).html(postHTML);
  $( "div#reply-to-post"+replyID ).append('<input type = "button" value = "cancel" class = "bbtn" onclick = "stopDigitizing()">');
  $( "div#reply-to-post"+replyID ).show("fast");
  typeSelect = document.getElementById('type');
  typeSelect.onchange = function(e) {
	map.removeInteraction(draw);
	addInteraction();
}

}

function showReplies(postid) {
if ($( "div#replies-to-" + postid).css( "display") == "none") {
  $( "div#replies-to-" + postid).css( "display", "block");
  $( "input#expand-replies-to" + postid).val("-");
}
else {
  $( "div#replies-to-" + postid).css( "display", "none");
  $( "input#expand-replies-to" + postid).val("+");
}
}

function stopDigitizing(threadid) {
digitizing = false;
map.removeInteraction(draw);
map.removeInteraction(select);
map.removeInteraction(modify);
vsource.clear();
$( "#postToThread"+threadid ).html('');
$( "#postToThread"+threadid ).hide("fast");
selectExisting=false;
$( "div#reply-to-post"+replyID ).html("");
$( "div#addNewThread" ).html("");
$( "div#addNewThread" ).hide("fast");
$( "#addtothread"+threadid).on({
 "mouseover" : function() {
    this.src = 'images/addhover.png';
  },
  "mouseout" : function() {
    this.src='images/add.png';
  }
});
  $( "#addtothread"+threadid).attr("onclick","postToThread("+threadid+")");
  $( "div#reply-to-post"+replyID ).hide("fast");
}


function updateVote(user,post,vote) {
  var ajaxRequest = new XMLHttpRequest();
  ajaxRequest.onreadystatechange=function() {
  if (ajaxRequest.readyState==4 && ajaxRequest.status==200) {
    highlightObject(ajaxRequest.responseText);
  }
  }
  var querystring = "?u="+user+"&p="+post+"&v="+vote;
  ajaxRequest.open("GET", "serverops/saveVote.php"+querystring, true);
  ajaxRequest.send();
  }

function zoomTo(objid) {
  var ajaxRequest = new XMLHttpRequest();
  ajaxRequest.onreadystatechange=function() {
  if (ajaxRequest.readyState==4 && ajaxRequest.status==200) {
     var responsedata = ajaxRequest.responseText;
     var bounds_array = responsedata.split(",");
     if (responsedata == ", , , ") alert("no geography");
      else if (bounds_array[1] == bounds_array[3]) {
       map.getView().fitExtent([parseFloat(bounds_array[0]), parseFloat(bounds_array[1]), parseFloat(bounds_array[2]), parseFloat(bounds_array[3])], map.getSize());
         map.getView().setZoom(16);
      }
      else map.getView().fitExtent([parseFloat(bounds_array[0]), parseFloat(bounds_array[1]), parseFloat(bounds_array[2]), parseFloat(bounds_array[3])], map.getSize());
  }}
  var querystring = "?obj="+objid;
  ajaxRequest.open("GET", "serverops/zoomTo.php"+querystring, true);
  ajaxRequest.send();
  }

function deletePost(postid) {
  var ajaxRequest = new XMLHttpRequest();
  ajaxRequest.onreadystatechange=function() {
  if (ajaxRequest.readyState==4 && ajaxRequest.status==200) {
    recentPosts();
  }}

  ajaxRequest.open("POST", "serverops/deletePost.php", true);
  ajaxRequest.setRequestHeader("Content-type","application/x-www-form-urlencoded");
  ajaxRequest.send("postid="+postid);
  }

