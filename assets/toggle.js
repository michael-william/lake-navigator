// document.addEventListener('DOMContentLoaded', function() {
//     var menuButton = document.getElementById('menu-button');

//     if (menuButton) {
//         console.log('Menu button found:', menuButton);
        
//         // Function to handle the click event
//         function handleClick() {
//             console.log('Menu button clicked');
//             var routePane = document.getElementById('route-info');
//             if (routePane) {
//                 routePane.classList.toggle('show');
//                 console.log('Route pane classes:', routePane.classList);
//             } else {
//                 console.error('Route pane not found.');
//             }
//         }

//         // Attach the click event listener to the menu button
//         menuButton.addEventListener('click', handleClick);

//         // Use MutationObserver to wait for route-info to be added to the DOM
//         var observer = new MutationObserver(function(mutations) {
//             mutations.forEach(function(mutation) {
//                 mutation.addedNodes.forEach(function(node) {
//                     if (node.id === 'route-info') {
//                         console.log('route-info added to DOM');
//                         // You can now safely interact with route-info
//                         observer.disconnect(); // Stop observing
//                     }
//                 });
//             });
//         });

//         // Start observing the document body for childList changes
//         observer.observe(document.body, { childList: true, subtree: true });
//     } else {
//         console.error('Menu button not found.');
//     }
// });
// var menuButton = document.getElementById('menu-button');
// console.log(menuButton);
// console.log(routePane);
// var routePane = document.getElementById('route-info');

// if (menuButton) {
//     menuButton.addEventListener('click', function() {
//                 console.log('Menu button clicked'); // Log when the button is clicked
//                 routePane.classList.toggle('show');
//                 console.log('Left pane classes:', routePane.classList); // Log the classes of the left pane
//             });
// }