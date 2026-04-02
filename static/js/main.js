const switchForm = document.getElementById('switchForm');
const switchElement = document.getElementById('my-switch');

// Add a submit event listener to the form
switchForm.addEventListener('submit', (event) => {
  // Prevent the form from submitting normally
  event.preventDefault();

  // Check if the switch is checked
  if (switchElement.checked) {
    // Disable the switch on other pages
    localStorage.setItem('switchState', 'on');
  } else {
    // Enable the switch on other pages
    localStorage.setItem('switchState', 'off');
  }
});

// Check if the switch is already on before enabling the switch
const switchState = localStorage.getItem('switchState');

if (switchState === 'on') {
  switchElement.disabled = true;

  // Add a click event listener to the switch to show an alert
  switchElement.addEventListener('click', () => {
    alert('Switch is already enabled on another page.');
  });
} else {
  switchElement.disabled = false;
}

// Add a click event listener to the switch to disable it on page 1
if (window.location.pathname === '/page1.html') {
  switchElement.addEventListener('click', () => {
    if (switchElement.checked) {
      switchElement.disabled = true;
      localStorage.setItem('switchState', 'on');
    }
  });
}

// Add a click event listener to the switch to disable it on page 2
if (window.location.pathname === '/page2.html') {
  switchElement.addEventListener('click', () => {
    if (switchElement.checked) {
      switchElement.disabled = true;
      localStorage.setItem('switchState', 'on');
    }
  });
}

// Add a load event listener to the window to enable the switch on page 2
window.addEventListener('load', () => {
  if (window.location.pathname === '/page2.html') {
    const switchState = localStorage.getItem('switchState');
    if (switchState === 'on') {
      switchElement.disabled = true;
    }
  }
});