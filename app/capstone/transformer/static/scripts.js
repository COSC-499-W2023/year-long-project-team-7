let lightMode = localStorage.getItem("lightMode");

const enableLightMode = () => {
    document.body.classList.add("lightmode");
    localStorage.setItem("lightMode", "enabled");
};

const disableLightMode = () => {
    document.body.classList.remove("lightmode");
    localStorage.setItem("lightMode", "disabled");
};

addEventListener("load", () => {
    if (lightMode === "enabled") {
        enableLightMode();
    }
});

$(document).ready(function () {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))


    $(".file-download-button").click(function () {
        const fileUrl = $(this).attr("data-fileurl");
        window.location.href = fileUrl;
    });

    
    $("#transform-file-upload").on("change", function (event) {
        $("#selected-file-names").empty();

        Array.from(event.target.files).forEach((file) => {
            $("#selected-input-file-names").append(`<p>${file.name}</p>`);
        });
    });

    $("#transform-template-file-upload").on("change", function (event) {
        $('input[name="template"]').prop('checked', false);
        $("#selected-template-file-name").empty();
        $("#selected-template-file-name").append(`<p>${event.target.files[0].name}</p>`);
    })

    $('input[type=radio][name=template]').on("click", function (event) {
        $("#selected-template-file-name").empty();
        $('#transform-template-file-upload').val('');
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

    $("#id_image_frequency").on("input change", function () {
        var value = $(this).val();
        var text = "Default";
        if (value == 0) text = "None";
        else if (value == 1) text = "A Few";
        else if (value == 2) text = "Some";
        else if (value == 3) text = "Default";
        else if (value == 4) text = "Many";
        else if (value == 5) text = "Numerous";
        else if (value == 6) text = "Lots";
        $("#image_frequency_value").text(text);
    });

    $("#id_num_slides").on("input change", function () {
        var value = $(this).val();
        $("#num_slides_value").text(value);
    });

    $(".template-choice").click(function () {
        $(this).find('input[type="radio"]').prop("checked", true);
    });

    $(".loading-overlay").hide();

    $("#generator-form").on("submit", function (event) {
        $(".loading-overlay").show();
    });

    $("#light-mode-toggle").on("click", function () {
        if (lightMode !== "enabled") {
            enableLightMode();
        } else {
            disableLightMode();
        }
        lightMode = localStorage.getItem("lightMode");
    });

    $('.template-choice input[type="radio"]').on('keydown', function(event) {
        if (event.keyCode === 13) {
            $(this).click();
        }
    });

});
