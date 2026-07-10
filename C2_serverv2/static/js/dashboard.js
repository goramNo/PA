async function loadDashboard() {

    try {

        const response = await fetch("/api/logs");

        const logs = await response.json();

        if (!logs || logs.length === 0) {

            document.getElementById("agentCount").textContent = "0";
            document.getElementById("hostCount").textContent = "0";
            document.getElementById("portCount").textContent = "0";
            document.getElementById("lastScan").textContent = "--";

            document.getElementById("agentContainer").innerHTML =
                "<h2>Aucune donnée reçue.</h2>";

            return;
        }

        // -------- Comptage des agents uniques --------

        const agents = new Set();

        logs.forEach(log => {

            if (log.data && log.data.agent) {

                agents.add(log.data.agent.hostname);

            }

        });

        document.getElementById("agentCount").textContent = agents.size;

        // -------- Dernier scan --------

        const latest = logs[0];

        const data = latest.data;

        document.getElementById("lastScan").textContent =
            latest.timestamp.substring(11, 19);

        let hostCount = 0;
        let portCount = 0;

        let html = "";

        if (data.modules && data.modules.scanner) {

            const scanner = data.modules.scanner;

            hostCount = scanner.hosts.length;

            document.getElementById("hostCount").textContent = hostCount;

            html += `

            <div class="agent">

                <h2>🟢 ${data.agent.hostname}</h2>

                <div class="agentInfo">

                    <p><b>Mode :</b> ${data.agent.mode}</p>

                    <p><b>Dernier contact :</b> ${data.agent.timestamp}</p>

                    <p class="online">ONLINE</p>

                </div>

            `;

            scanner.hosts.forEach(host => {

                html += `

                <div class="host">

                    <h3>${host.ip}</h3>

                `;

                if (host.hostname) {

                    html += `
                    <p><b>Hostname :</b> ${host.hostname}</p>
                    `;

                }

                let openFound = false;

                host.ports.forEach(port => {

                    if (port.state !== "open")
                        return;

                    openFound = true;

                    portCount++;

                    html += `

                    <span class="badge">

                        ${port.port}/tcp ${port.service}

                    </span>

                    `;

                });

                if (!openFound) {

                    html += `
                    <p>Aucun port ouvert détecté.</p>
                    `;

                }

                html += `

                </div>

                `;

            });

            html += "</div>";

        }

        document.getElementById("portCount").textContent = portCount;

        document.getElementById("agentContainer").innerHTML = html;

    }

    catch (error) {

        console.error(error);

        document.getElementById("agentContainer").innerHTML =
            "<h2>Impossible de contacter le serveur.</h2>";

    }

}

loadDashboard();

setInterval(loadDashboard, 3000);