document.addEventListener("DOMContentLoaded", function() {
    const logsBody = document.getElementById('logsBody');

    fetch('http://localhost:3000/api/logs')
        .then(response => response.json())
        .then(data => {
            const logs = data.logs;
            logs.forEach(log => {
                const row = document.createElement('tr');

                const zoneCell = document.createElement('td');
                zoneCell.textContent = log.zone_number;
                row.appendChild(zoneCell);

                const deviceCell = document.createElement('td');
                deviceCell.textContent = log.device_name;
                row.appendChild(deviceCell);

                const statusCell = document.createElement('td');
                statusCell.textContent = log.status;
                row.appendChild(statusCell);

                const dataCell = document.createElement('td');
                dataCell.textContent = log.data;
                row.appendChild(dataCell);

                const timeCell = document.createElement('td');
                timeCell.textContent = log.time;
                row.appendChild(timeCell);

                logsBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error fetching logs:', error);
        });
});





















document.addEventListener("DOMContentLoaded", function() {
    const logsBody = document.getElementById('logsBody');

    fetch('http://localhost:3000/api/logs')
        .then(response => response.json())
        .then(data => {
            const logs = data.logs;
            logs.forEach(log => {
                const row = document.createElement('tr');

                const zoneCell = document.createElement('td');
                zoneCell.textContent = log.zone_number;
                row.appendChild(zoneCell);

                const deviceCell = document.createElement('td');
                deviceCell.textContent = log.device_name;
                row.appendChild(deviceCell);

                const statusCell = document.createElement('td');
                statusCell.textContent = log.status;
                row.appendChild(statusCell);

                const dataCell = document.createElement('td');
                dataCell.textContent = log.data;
                row.appendChild(dataCell);

                const timeCell = document.createElement('td');
                timeCell.textContent = log.time;
                row.appendChild(timeCell);

                logsBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error fetching logs:', error);
        });
        
        setTimeout(function(){
                location.reload();},10000);
});
