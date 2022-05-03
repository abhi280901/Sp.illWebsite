$(function(){
    $('#clear').submit(function() {
        return false;
    });
    
    $("#clear").click(function(){
        $.ajax({
            type : 'POST',
            url : '/spec2',
            data: $('#clear').serialize(),
            success : function(data){
                $('#form').html("<p>This debt to you have been updated!</p>");
                $('#form').css('color','#66FF99');
                if(data.status == 1)
                $('#status').html("Cleared");
                else
                $('#status').html("Pending");
                $('#value').html(data.value);
                $('#status').css('color','#66FF99');
                $('#value').css('color','#66FF99');
            }
        })
    })

    $('#revert').submit(function() {
        return false;
    });
    

    $("#revert").click(function(){
        $.ajax({
            type : 'POST',
            url : '/revert',
            data: $('#revert').serialize(),
            success : function(data){
                $('#form').html("<p>This debt have been reverted!</p>");
                $('#form').css('color','#FF0000');
                $('#status').html('Pending');
            }
        }) 
        
    })
})