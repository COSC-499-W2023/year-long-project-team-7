$(document).ready(function () {
    $("#file-download-button").click(function () {
        const fileUrl = $(this).attr("data-fileurl");
        window.location.href = fileUrl;
    });

    $("#transform-file-upload").on("change", function (event) {
        $("#selected-file-names").empty();

        Array.from(event.target.files).forEach((file) => {
            console.log(file);
            $("#selected-file-names").append(`<p>${file.name}</p>`);
        });
    });

    $("#id_complexity").on("input change", function () {
        var value = $(this).val();
        var text = "Default";
        if (value == 0) text = "Very Basic";
        else if (value == 1) text = "Basic";
        else if (value == 2) text = "Moderate";
        else if (value == 3) text = "Default";
        else if (value == 4) text = "Highly Advanced";
        else if (value == 5) text = "Very Detailed";
        else if (value == 6) text = "Extremely Detailed";
        $("#complexity_value").text(text);
    });

    $("#id_num_images").on("input change", function () {
        var value = $(this).val();
        var text = "Default";
        if (value == 0) text = "None";
        else if (value == 1) text = "A Few";
        else if (value == 2) text = "Some";
        else if (value == 3) text = "Default";
        else if (value == 4) text = "Many";
        else if (value == 5) text = "Numerous";
        else if (value == 6) text = "Lots";
        $("#num_images_value").text(text);
    });

    $("#id_num_slides").on("input change", function () {
        var value = $(this).val();
        $("#num_slides_value").text(value);
    });

    $(".template-choice").click(function () {
        $(this).find('input[type="radio"]').prop("checked", true);
    });

    $(".loading-overlay").show();

    // $(".loading-overlay").hide();
});
