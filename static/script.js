// document.addEventListener("DOMContentLoaded", () => {
//     const jobTextForm = document.getElementById("jobTextForm");
//     const jobFileForm = document.getElementById("jobFileForm");
//
//     // Toggle visibility of forms
//     function toggleInput() {
//         const jobInputType = document.querySelector('input[name="job_input_type"]:checked').value;
//
//         if (jobInputType === "text") {
//             jobTextForm.style.display = "block";
//             jobFileForm.style.display = "none";
//         } else if (jobInputType === "file") {
//             jobTextForm.style.display = "none";
//             jobFileForm.style.display = "block";
//         }
//     }
//
//     toggleInput();
//
//     // Event listener for radio buttons
//     const radios = document.querySelectorAll('input[name="job_input_type"]');
//     radios.forEach((radio) => {
//         radio.addEventListener("change", toggleInput);
//     });
// });
//
//
const radioButtons = document.querySelectorAll('input[name="input-type"]');
const jobTextContainer = document.getElementById('jobTextContainer');
const jobFileContainer = document.getElementById('jobFileContainer');

radioButtons.forEach(radio => {
    radio.addEventListener('change', () => {
        if (radio.value === 'text') {
            jobTextContainer.style.display = 'block';
            jobFileContainer.style.display = 'none';
        } else {
            jobTextContainer.style.display = 'none';
            jobFileContainer.style.display = 'block';
        }
    });
});

// Modal logic
function confirmDelete(url) {
    const modal = document.getElementById('deleteModal');
    const form = document.getElementById('deleteForm');
    form.action = url;
    modal.style.display = 'block';
}

function closeModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

// Close modal if clicked outside content
window.onclick = function(event) {
    const modal = document.getElementById('deleteModal');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

