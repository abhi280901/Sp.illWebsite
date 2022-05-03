$(function(){
    var bill_id = $('.table').attr('id');
    if ($('#debtors tbody tr').length == 0) {
        $.ajax({
            type : 'POST',
            url : '/rembill',
            data : {'bill_id': bill_id},
            success : function(){
                $('.table').html('')
                $('#message').html("<p> All debts for this bill has been cleared.</br> This bill will no longer appear on your home page</p><p> Click <a href=\"/home\">here to return to the home page")
                $('#message').css('color','#66FF99')
            }
        })
    }
})