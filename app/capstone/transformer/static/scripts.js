$(document).ready(function() {

    $('.file-download-button').click(function() {
        const fileUrl = $(this).attr('data-fileurl');
        window.location.href = fileUrl;
    });
}) 
