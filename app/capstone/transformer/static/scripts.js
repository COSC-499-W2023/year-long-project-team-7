$(document).ready(function(){

    $('.file-download-button').click(function() {
        const fileUrl = $(this).attr('data-fileurl');
        window.location.href = fileUrl;
    });

    $('#transform-file-upload').on('change', function(event){
        $("#selected-file-names").empty();

        Array.from(event.target.files).forEach(file => {
            console.log(file)
            $("#selected-file-names").append(`<p>${file.name}</p>`);
        });
    });
});


