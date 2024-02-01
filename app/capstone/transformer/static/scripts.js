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


function pdfPreview(){
    pdfjsLib.GlobalWorkerOptions.workerSrc =  "https://cdn.jsdelivr.net/npm/pdfjs-dist@2.7.570/build/pdf.worker.min.js";
                                
    const pdfContainer = document.getElementById("pdf-container");
    const pdf = $('#pdf-file').val();

    let currentPage = 1;

    const showPage = function (pageNum) {
        pdfjsLib
            .getDocument(pdf)
            .promise.then((pdfDoc) => {
                return pdfDoc.getPage(pageNum);
            })
            .then((page) => {
                const scale = 1;
                const viewport = page.getViewport({ scale });
    
                const canvas = document.getElementById("pdf-canvas");
                const context = canvas.getContext("2d");
                canvas.height = viewport.height;
                canvas.width = viewport.width;
                pdfContainer.appendChild(canvas);
    
                const renderContext = {
                    canvasContext: context,
                    viewport: viewport,
                };
                const renderTask = page.render(renderContext);
                currentPage = pageNum;
                return renderTask.promise;
            })
            .catch((error) => {
                console.error("Error loading PDF:", error);
            });
    };

    showPage(currentPage);
}

$(document).ready(function () {

    if($("#pdf-file").length > 0){
        console.log("asdgfasdf")
        pdfPreview();
    }

    $(".file-download-button").click(function () {
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

    // Reference the showPage function from results.html
    const pdfPreviewScript = document.getElementById("pdf-preview-script");
    if (pdfPreviewScript) {
        eval(pdfPreviewScript.text);
    }

    // Event listener
    $("#next-button").on("click", function () {
        // This function is defined in results.html
        showPage(currentPage + 1);
    });

    $("#prev-button").on("click", function () {
        showPage(currentPage - 1);
    });

    $("#light-mode-toggle").on("click", function () {
        if (lightMode !== "enabled") {
            enableLightMode();
        } else {
            disableLightMode();
        }
        lightMode = localStorage.getItem("lightMode");
    });
});
