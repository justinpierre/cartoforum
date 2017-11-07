function jqueryTest() {
  $.getJSON($SCRIPT_ROOT + '/_jquerytest', {
  }, function(data){
     alert(data.result)
  });
}