const searchField = document.querySelector('#searchField');
const tableOutput = document.querySelector('.table-output');
const appTable = document.querySelector('.app-table');
const paginationContainer = document.querySelector('.pagination-conatiner');
const tBody = document.querySelector('.table-body');
tableOutput.style.display = "none";

searchField.addEventListener('keyup', (e)=>{
    const searchValue = e.target.value;

    if (searchValue.trim().length >0){
        paginationContainer.style.display = 'none';
        tBody.innerHTML = ""
        fetch("/income/search-income", {
            body: JSON.stringify({ 'searchText': searchValue }),
            method: "POST",
          })
            .then((res) => res.json())
            .then((data) => {
                console.log('data', data);
                appTable.style.display = 'none';
                tableOutput.style.display = 'block';
                if (data.length === 0){
                    tableOutput.innerHTML = 'No results found';
                }else{
                    data.forEach(item => {
                        tBody.innerHTML += `
                    <tr>
                        <td>${item.amount}</td>
                        <td>${item.source}</td>
                        <td>${item.description}</td>
                        <td>${item.date}</td>
                    </tr>`;
                    });
                    
                }
            });
    }else{
        tableOutput.style.display = 'none';
        appTable.style.display = 'block';
        tableOutput.style.display = 'none';
        paginationContainer.style.display = 'block';
    }
});