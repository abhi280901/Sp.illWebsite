$(function(){
    var x = $('.spill').attr('id')
    $('#no').click(function(){
        $('#form-settle').html(
            "<p><label>Value settled: </label><input type='number'  name='value' id='value' required/></p>"
        )
        $('#value').attr('id','value')
    })
    $('#yes').click(function(){
        $('#form-settle').html(
            ""
        )
    })
    $('.spill').submit(function(){
        var y = $('#value').val();
        if((y<=x)||(y==null)){
            return true;
        }
        else{
            $('#value-validate').html(
                '<p>Value entered exceeds your debt value. If you can clear the whole debt, please select the corresponding option.</p>'
                )
            $('#value-validate').css('color','red');
            return false;
        }
    })
})