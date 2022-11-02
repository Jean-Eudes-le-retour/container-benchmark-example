import RobotWindow from 'https://cyberbotics.com/wwi/R2022b/RobotWindow.js';

window.robotWindow = new RobotWindow();
const benchmarkName = 'Robot Programming';
let benchmarkPerformance = 0;

window.robotWindow.receive = function(message, robot) {
  if (message.startsWith('percent:'))
    document.getElementById('achievement').innerHTML = metricToString(parseFloat(message.substr(8)));
  else if (message.startsWith('success:')) {
    const newMessage = message.replace('success', 'confirm');
    this.send(newMessage)
    benchmarkPerformance = message.split(':')[2]
    const benchmarkPerformanceString = metricToString(benchmarkPerformance);
    document.getElementById('achievement').innerHTML = benchmarkPerformanceString;
    document.getElementById('achievement').style.color = 'green';
    // do we need a cleaner way of doing this?
    alert(
    `           ${benchmarkName} complete
    Congratulations you finished the benchmark!
    
    Your current performance is: ${benchmarkPerformanceString}.
    
    If you want to submit your controller to the leaderboard, follow the instructions given by the "Register" button on the benchmark page.`
    )
  } else
    console.log("Received unknown message for robot '" + robot + "': '" + message + "'");

  function metricToString(metric) {
    return (metric * 100).toFixed(2) + '%';
  }
};
