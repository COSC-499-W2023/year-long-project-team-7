// function updateFilename(input) {
//     const selectedFile = input.files[0];
//     const fileNameDisplay = document.getElementById("selected-file-name");

//     if (selectedFile) {
//         fileNameDisplay.textContent = `${selectedFile.name}`;
//     } else {
//         fileNameDisplay.textContent = "No file selected";
//     }
// }

// $(document).ready(updateFilename);



$(document).ready(function(){
    $('.file-download-button').click(function() {
        const fileUrl = $(this).attr('data-fileurl');
        window.location.href = fileUrl;
    });
})

