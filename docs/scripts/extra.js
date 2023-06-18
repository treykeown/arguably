$(document).ready(function() {
    // Make non-python code blocks have a gray border instead of green
    $(".highlight:has(:contains('user@machine'))").addClass("lang-console");
    $(".highlight:has(:contains('Before: '))").addClass("lang-other");
});
