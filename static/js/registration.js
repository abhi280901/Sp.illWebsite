$( function(){
      
$('#yes').click(function(){
    $('#form-hhold').html(
        "<p><label>Household reference code: </label><input type='text' name='hhold_code' placeholder='Enter your household reference id' id='hhold_code' required/><div id='form-hid'></div></p>"
    )
})

$('#no').click(function(){
    $('#form-hhold').html(
        "<p><label>Household name: </label><input type='text' name='hhold_name' placeholder='Name your household' id='hhold_name' required/><div id='form-hid'></div></p>"
        )
})


$('#regform').submit(function() {
    var x = $('#pswrd').val();
    var y = $('#repswrd').val(); 
    if(x == y){
        return true;
    }
    else{
        $('#form-repassword').html("Your passwords do not match! Please re-enter them.")
        $('#form-repassword').css("color","red")
        return false;
    }
});

});