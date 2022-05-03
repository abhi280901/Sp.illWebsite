$(function(){
    
    $('.notf').click(function(){
        var id = $(this).attr('id');
        $.ajax({
            type : 'POST',
            url : '/not',
            data : {"not_id":id},
            success : function(data){
                $('#content').html(data.content)
                $('#content').css('color','#66FF99');

            }
        })
    })
})