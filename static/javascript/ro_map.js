var map, typeSelect, draw, vector, groupobjectssrc, groupobjects, overlay, container, content, closer, selectedObjectSrc, selectedobject, selectExisting, digitizing, modify, select, threadsrc,light,dark;
var replyID = null;


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
      source: new ol.source.XYZ({url: 'https://s.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'}),
      sphericalMercator: true,
      attributions: [new ol.Attribution({ html: ['&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://cartodb.com/attributions">CartoDB</a>'] })]
    });

dark = new ol.layer.Tile({
      visible:false,
      source: new ol.source.XYZ({url: 'https://s.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'}),
      sphericalMercator: true,
      attributions: [new ol.Attribution({ html: ['&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://cartodb.com/attributions">CartoDB</a>'] })]
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
url: 'https://cartoforum.com:8443/geoserver/wms',
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
  url = "https://cartoforum.com" + url.substring(22);
  url="/_discovery_popup?url="+encodeURIComponent(url);

  var xmlhttp = new XMLHttpRequest();
  xmlhttp.onreadystatechange=function() {
	  if (xmlhttp.readyState==4 && xmlhttp.status==200) {
	    var xmlDoc = xmlhttp.responseText;
	    if (xmlDoc.search("class")!=-1 && xmlDoc.search("No QUERY_LAYERS has been requested, or no queriable layer in the request anyways")==-1 && xmlDoc) {
	      content.innerHTML = xmlDoc;
              $( "#objinfo" ).show( "fast" );
	      var x = content.getElementsByTagName("td");
	      if (selectExisting){
	       selectExisting = x[1].innerHTML;
	       }
	      else {
	      $( "#objid" ).html(x[1].innerHTML);

}
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


getGroupThreads()

$('#filter-by-thread').change(function(){
  var threadid = $(this).find(':selected').val();
  if (threadid == "new") newThread();
  else if (threadid != "none") {
     $.getJSON($SCRIPT_ROOT + '/_get_thread_posts',{
       threadid: threadid
     },
     function (response) {
         $("#posts").html("")
       for (var i in response.threads) {
         var newthread = "<div id = 'threadname'><div style = 'margin-right: 30px'>" + response.threads[i]['name'] + '</div>';
         newthread += '<img class = "addpost" id = "addtothread' + response.threads[i]['threadid'] + '" src = "/static/images/add.png" onclick = "postToThread(' + response.threads[i]['threadid'] + ')" data-toggle="tooltip" title="Add to thread"><span class = "clickinst">Click to add a post</span></div>';
         newthread += '<div class = "postToThread" id = "postToThread' + response.threads[i]['threadid'] + '"></div>';
         $("#posts").append(newthread);
         for (var j=0; j< response.threads[i]['posts'].length; j++) {
          var newpost = createPost(response.threads[i]['posts'][j]);
          $("#posts").append(newpost);
         }
       }
       });
     threadsrc = new ol.source.TileWMS(/** @type {olx.source.TileWMSOptions} */ ({
     url: 'https://cartoforum.com:8443/geoserver/wms',
                params: {'LAYERS': 'Argoomap_postgis:threadview', 'TRANSPARENT': true, 'TILED': false, 'viewparams': 'groupid:'+groupid+';threadid:'+threadid},
		serverType: 'geoserver'
	     }));
    groupobjects.setSource(threadsrc);
  }
  else groupobjects.setSource(groupobjectssrc);
});
$('#filter-by-thread').trigger('change');

//populate user filter on click
  $.getJSON($SCRIPT_ROOT + '/_get_group_users',
  function (response) {
    for (var i in response.users) {
      $('#filter-by-user').append($('<option/>', {
        value: response.users[i]['userid'],
        text: response.users[i]['name']
        }));
      }
  })


//filter posts by user
$('#filter-by-user').change(function() {
 var userfilter = $(this).find(':selected').val();
 if (userfilter != "none") {
 $( '#createThread' ).html( '' );
  var userid = $(this).find(':selected').val();
   $.getJSON($SCRIPT_ROOT + '/_user_posts',{
        userid: userid
   }, function (response) {
            $("#posts").html("")
            for (var i = 0; i<response.posts.length;i++) {
                var newpost = createPost(response.posts[i]);
                $("#posts").append(newpost);
            }
        });
   threadsrc = new ol.source.TileWMS(/** @type {olx.source.TileWMSOptions} */ ({
     url: 'https://cartoforum.com:8443/geoserver/wms',
                params: {'LAYERS': 'Argoomap_postgis:userobjects', 'TRANSPARENT': true, 'TILED': false, 'viewparams': 'groupid:'+groupid+';userid:'+userid},
		serverType: 'geoserver'
	     }));
	      groupobjects.setSource(threadsrc);
  }
});
$('#filter-by-user').trigger('change');

recentPosts();
}

//style toggle
function styleChange(color) {
  $("#selectedStyle").attr("src","static/images/"+color+".gif");
  groupobjectssrc.updateParams({STYLES: color});
  if (threadsrc) threadsrc.updateParams({STYLES: color});
  $( 'div#style-select-options' ).hide('fast');
}

function addInteraction() {
  digitizing = true;
  var value = typeSelect.options[typeSelect.selectedIndex].value;
  console.log(value);
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

function createPost(post){
    if (post[7]) vtotal = post[7];
    else vtotal = 0;
    if (post[11]) var indent = post[11] + 'px';
    else var indent = '0px';
    var newpost = "<div class = 'postContent' id = '" + post[0] + "' onClick = 'highlightObject(this.id, " + post[3] + ")' style = 'margin-left: " + indent + "'>";
    if (post[9]) newpost += "<div class = 'clickedPostTopBar'>";
    else  newpost += "<div class = 'postTopBar'>";
    newpost += "<p class = 'fromfind'>From: " + post[5] + "<span style = 'float: right;'>";
    if (post[3]) newpost += "<input type = 'button' class = 'btn findbtn' value = '&#x1f50d;' onclick = 'zoomTo(" + post[3] + ")'>";
    newpost += "</span></p>"
    newpost += "User " + post[6] + "<span style = 'float: right; font-size: 8px;'>\n Date " + post[2] + "</span></div>";
    var content = anchorme(post[4],{
	  attributes:[
		function(urlObj){
			if(urlObj.protocol !== "mailto:") return {name:"target",value:"blank"};
		}
	  ]
    });
    if (content.includes('<a href="')) {
        var target = content.substring(content.indexOf('<a href="')+9,content.indexOf('>')-2);
        $.ajax({
          url: "https://api.linkpreview.net",
          type: 'GET',
          async: false,
          dataType: 'jsonp',
          data: {q: target, key: '5adb7c702abd3ef92ec48a92ac86384c1c08a8651fb72'},
          success: function (response) {
            console.log(response);
            if (response['error'] != 424) {
              $("#" + post[0]).append("<img class = 'imgpreview' src = '" + response['image'] + "'>");
              $("#" + post[0]).append("<p class = 'imgtitle'>" + response['title'] + "</p>");
              }
            }
        });
    }
    newpost += "<div class = 'postText'>" + post[4] + "</div></div>";
    newpost += "<div class = 'replyToPostContainer' style = 'margin-left: " + indent + "'>";

  newpost += "<a href = '#' ><img class = 'votebtns' src='/static/images/minus.png'></a><span class = 'vtotal'>";
  newpost += vtotal + "</span><a href = '#''><img class = 'votebtns' src='/static/images/plus.png'></a></a>";

    return newpost
}

function recentPosts() {
 $( '#posts').html("");
$.getJSON($SCRIPT_ROOT + '/_recent_posts',
  function (response) {
            for (var i = 0; i<response.posts.length;i++) {
                var newpost = createPost(response.posts[i]);
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

function getGroupThreads() {
  $( '#createThread' ).html( '' );
  $.getJSON($SCRIPT_ROOT + '/_get_group_threads',
  function (response) {
  for (var i in response.threads) {
      $('#filter-by-thread').append($('<option/>', {
      value: response.threads[i]['threadid'],
      text: response.threads[i]['name']
      }));
  }})
}

function postExtent() { 
  var extent = map.getView().calculateExtent(map.getSize());
  var bottomLeft = ol.extent.getBottomLeft(extent);
  var topRight = ol.extent.getTopRight(extent);
  var bounds = bottomLeft[0] + " " + bottomLeft[1] + " " + topRight[0] + " " + topRight[1];

 $( '#createThread' ).html( '' );
 $( '#posts').html("");
 $.getJSON($SCRIPT_ROOT + '_posts_by_extent',
 {ext: bounds},
 function (response) {
    for (var i = 0; i<response.posts.length;i++) {
                var newpost = createPost(response.posts[i]);
                $("#posts").append(newpost);
            }
 });
   $( '#filter-by-user' ).val("none");
   $( '#filter-by-thread' ).val("none");
  groupobjects.setSource(groupobjectssrc);
}

function searchPosts() {
$( '#createThread' ).html( '' );
$("#posts").html("")
 var searchstring = $( "#searchPosts" ).val();
 if (searchstring=="") return;
 $( '#createThread' ).html( '' );
 $.getJSON($SCRIPT_ROOT + '_search_posts', {
   q: searchstring
 },
 function (response){
for (var i = 0; i<response.posts.length;i++) {
                var newpost = createPost(response.posts[i]);
                $("#posts").append(newpost);
            }

 });
 $( '#filter-by-user' ).val("none");
 $( '#filter-by-thread' ).val("none");
 groupobjects.setSource(groupobjectssrc);
}


function highlightObject(postid, objid) {
    if (selectedObjectSrc) selectedobject.setSource();
    if (objid) {
      selectedObjectSrc = new ol.source.TileWMS(/** @type {olx.source.TileWMSOptions} */ ({
      url: 'https://cartoforum.com:8443/geoserver/wms',
                params: {'LAYERS': 'Argoomap_postgis:SelectedFeatures', 'TRANSPARENT': true, 'TILED': false, 'viewparams': 'objid:'+objid},
		serverType: 'geoserver'
	     }));
      selectedobject = new ol.layer.Tile({source: selectedObjectSrc, visible: true});
      map.addLayer(selectedobject);
    }
  if (selectExisting) return;
  if (!postid) {
   var data_type = 'objid';
   var id = objid;
  }
  else{
    var data_type = 'postid';
    var id = postid;
  }

  $.getJSON($SCRIPT_ROOT + '/_get_post', {
     id: id,
     type: data_type
  }, function (response) {
       $("#posts").html("")
       for (var key in response.data) {
         console.log(key);
         var newthread = "<div id = 'threadname'><div style = 'margin-right: 30px'>" + response.data[key].name + '</div></div';
         newthread += '<div class = "postToThread" id = "postToThread' + key + '"></div>';
         $("#posts").append(newthread);
         for (var i=0; i< response.data[key].posts.length; i++) {
          var newpost = createPost(response.data[key].posts[i]);
          $("#posts").append(newpost);
         }
       }
       //$(".clickedPostTopBar").addClass("postTopBar");
       //$(".clickedPostTopBar").removeClass("clickedPostTopBar");
       if (!postid) {
         $('#sidebar').animate({
           scrollTop: $(".clickedPostTopBar").offset().top-140
         }, 2000);
       }
    }
 )
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

function zoomTo(objid) {
  $.getJSON($SCRIPT_ROOT + '/_zoom_to', {
    objid: objid
    }, function (response) {
     var bounds_array = response.bounds.split(",");
     if (response.bounds == ", , , ") alert("no geography");
      else if (bounds_array[1] == bounds_array[3]) {
       map.getView().fit([parseFloat(bounds_array[0]), parseFloat(bounds_array[1]), parseFloat(bounds_array[2]), parseFloat(bounds_array[3])], map.getSize());
         map.getView().setZoom(16);
      }
      else map.getView().fit([parseFloat(bounds_array[0]), parseFloat(bounds_array[1]), parseFloat(bounds_array[2]), parseFloat(bounds_array[3])], map.getSize());

  })
}
