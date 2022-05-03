$(function(){
    $('.deadline').each(function(){
        var debt_id = $(this).attr('id')
        var dtToday = new Date();
        var deadline = new Date($(this).html());
        if(deadline<dtToday){
            $.ajax({
                type : 'POST',
                url : 'overdue',
                data: {'debt_id':debt_id},
                success : function(data){
                    if (data.status == 3){
                        $('.'+data.id).css('background-color','red')
                    }

                }
            })
        }

    })
    
})