// Get the checkbox and slider elements from the DOM
const checkbox = document.querySelector("input[type='checkbox']");
const slider = document.querySelector(".slider");

// Set up an event listener for when the checkbox changes
checkbox.addEventListener("change", function() {
    // Check if the checkbox is checked
    if (checkbox.checked) {
        // Start skipping the promos
        // Add your code here
        console.log("skipping promos");
    } else {
        // Stop skipping the promos
        // Add your code here
        console.log("stopping promos");
    }
});
