$(document).ready(function () {
    let pdf = null
    let pdfContainer = null
    let currentPage = 1

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

    if($("#pdf-file").length > 0){
        pdfjsLib.GlobalWorkerOptions.workerSrc =  "https://cdn.jsdelivr.net/npm/pdfjs-dist@2.7.570/build/pdf.worker.min.js";
                                
        pdfContainer = document.getElementById("pdf-container");
        pdf = $('#pdf-file').val();


        showPage(currentPage);


        $("#next-button").on("click", function () {
            showPage(currentPage + 1);
        });
    
        $("#prev-button").on("click", function () {
            showPage(currentPage - 1);
        });
    }
});