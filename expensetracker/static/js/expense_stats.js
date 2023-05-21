function random_item(items)
{
  
return items[Math.floor(Math.random()*items.length)];
     
}

var items = ['bar', 'doughnut', 'pie', 'radar', 'line', 'polarArea'];

const renderChart = (data, labels) => {
  const ctx = document.getElementById("myChart");

  new Chart(ctx, {
    type: random_item(items),
    data: {
      labels: labels,
      datasets: [
        {
          label: "Last 6 months",
          data: data,
          backgroundColor:[
            "rgba(255,99,132,0.2)",
            "rgba(54,99,235,0.2)",
            "rgba(255,206,86,0.2)",
            "rgba(75,192,192,0.2)",
            "rgba(153,102,255,0.2)",
            "rgba(255,159,64,0.2)",
            ],
            borderColor:[
                "rgba(255,99,132,1)",
                "rgba(54,99,235,1)",
                "rgba(255,206,86,1)",
                "rgba(75,192,192,1)",
                "rgba(153,102,255,1)",
                "rgba(255,159,64,1)",
                ],
          borderWidth: 1,
        },
      ],
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
};

const getChartData = () => {
  fetch("expense-category-summary")
    .then((res) => res.json())
    .then((results) => {
      console.log(results);
      const category_data = results.expense_category_data;
      const [labels, data] = [Object.keys(category_data), Object.values(category_data)];

      renderChart(data, labels)
    });
};

document.onload = getChartData();
