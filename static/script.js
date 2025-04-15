document.addEventListener("DOMContentLoaded", () => {
    const jobTextForm = document.getElementById("jobTextForm");
    const jobFileForm = document.getElementById("jobFileForm");
    
    // Toggle visibility of forms
    function toggleInput() {
        const jobInputType = document.querySelector('input[name="job_input_type"]:checked').value;

        if (jobInputType === "text") {
            jobTextForm.style.display = "block";
            jobFileForm.style.display = "none";
        } else if (jobInputType === "file") {
            jobTextForm.style.display = "none";
            jobFileForm.style.display = "block";
        }
    }

    toggleInput();

    // Event listener for radio buttons
    const radios = document.querySelectorAll('input[name="job_input_type"]');
    radios.forEach((radio) => {
        radio.addEventListener("change", toggleInput);
    });
});

