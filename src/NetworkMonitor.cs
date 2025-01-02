using System.Diagnostics;
using System.Net.NetworkInformation;
using System.Text.Json;

namespace NetworkWidget
{
    public class NetworkMonitor
    {
        public string GetNetworkConnections()
        {
            var processes = Process.GetProcesses();
            var connections = IPGlobalProperties.GetIPGlobalProperties()
                                                 .GetActiveTcpConnections();

            var connectionData = connections.Select(c => new
            {
                LocalAddress = c.LocalEndPoint.Address.ToString(),
                RemoteAddress = c.RemoteEndPoint.Address.ToString(),
                State = c.State.ToString(),
                ProcessId = c.ProcessId,
                ProcessName = processes.FirstOrDefault(p => p.Id == c.ProcessId)?.ProcessName
            });

            return JsonSerializer.Serialize(connectionData);
        }
    }
}
