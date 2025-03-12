const baseUrl = "http://127.0.0.1:8000";

const brigades = []

function loadAll(query="") {
    const response = fetchBrigadesSync();
    document.getElementById('brigades-container').innerHTML = generateHtmlFromJson(response)
    const submits = fetchLabSubmits();
    document.getElementById('submitions-container').innerHTML = generateSubmitsHtmlFromJson(submits)
    document.getElementById('all-container').innerHTML = generateAll(response, submits, query);
}

async function createBrigade(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const num = formData.get('num');
    const students = formData.get('students');

    const response = await fetch(`${baseUrl}/brigades/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'accept': 'application/json'
        },
        body: JSON.stringify({
            num: parseInt(num, 10),
            students: students
        })
    });

    

    const result = await response.json();
    if (response.status != 200) {
        alert(result.detail);
    }
    console.log(result);
    loadAll();
}

function deleteLabSubmissionSync(submissionId) {
    if (!confirm(`Are you sure you want to delete this submission (${submissionId})?`)) {
        return;
    }
    const xhr = new XMLHttpRequest();
    xhr.open('DELETE', `${baseUrl}/labs/submissions/remove/${submissionId}`, false); 
    xhr.send();
    if (xhr.status !== 200) {
        return;
    }
    const data = JSON.parse(xhr.responseText);
    console.log(data.message); 
    loadAll();
}

function deleteBrigadeSync(brigadeId) {
    if (!confirm(`Are you sure you want to delete this brigade (${brigadeId})?`)) {
        return;
    }
    const xhr = new XMLHttpRequest();
    xhr.open('DELETE', `${baseUrl}/brigades/remove/${brigadeId}`, false);
    xhr.send();
    if (xhr.status !== 200) {
        return;
    }
    const data = JSON.parse(xhr.responseText);
    console.log(data.message);
    loadAll();
}

function fetchBrigadesSync() {
    const xhr = new XMLHttpRequest();
    const url = `${baseUrl}/brigades/all/`;

    xhr.open('GET', url, false);

    try {
        xhr.send();
        if (xhr.status === 200) {
            const response = xhr.response;
            let data = JSON.parse(response);
            data.sort(function(a, b) {
                return a.num - b.num;
            });
            return data;
        } else {
            return [];
        }
    } catch (error) {
        return [];
    }
}


function fetchLabSubmits() {
    const xhr = new XMLHttpRequest();
    const url = `${baseUrl}/labs/submissions/`;

    xhr.open('GET', url, false);

    try {
        xhr.send();
        if (xhr.status === 200) {
            const response = xhr.response;
            let data = JSON.parse(response)
            data.sort(function(a, b) {
                return a.brigade_num - b.brigade_num;
            });
            return data;
        } else {
            return [];
        }
    } catch (error) {
        return [];
    }
}

function generateHtmlFromJson(jsonArray) {
    let html = '';

    jsonArray.forEach(brigade => {
        const studentsList = brigade.students.join(', ');
        brigade_id = `brig${brigade.num}`
        
        html += `
            <div class="row">
                <div class="delete-col" onclick="deleteBrigadeSync('${brigade_id}')">
                    <i class="lni lni-trash-3"></i>
                </div>
                <div class="col1">
                    ${brigade.num}
                </div>
                <div class="col1">
                    ${studentsList}
                </div>
            </div>
        `;
    });
    return html;
}

function generateSubmitsHtmlFromJson(jsonArray) {
    let html = '';
    
    jsonArray.forEach(submit => {
        submition_id = `submission_${submit.brigade_num}_${submit.lab_num}_${submit.submission_date}`

        html += `
            <div class="row">
                <div class="delete-col" onclick="deleteLabSubmissionSync('${submition_id}')">
                    <i class="lni lni-trash-3"></i>
                </div>
                <div class="col2">
                    ${submit.brigade_num}
                </div>
                <div class="col2">
                    ${submit.lab_num}
                </div>
                <div class="col2">
                    ${submit.submission_date}
                </div>
            </div>
        `;
    });
    return html;
}


function generateAll(brigades, submits, query="") {
    let html = '';
    submits.forEach(submit => {
        brigade = brigades.find((brigade) => brigade.num == submit.brigade_num)
        
        if (brigade == undefined) {
            return;
        }
        
        let check = brigade.num.toString().toLowerCase() == query.toLowerCase() ||
                    submit.lab_num.toString().toLowerCase() == query.toLowerCase() ||
                    brigade.students.some(student => student.toLowerCase().includes(query.toLowerCase())) ||
                    submit.submission_date.toLowerCase() == query.toLowerCase();

        if (!check) {
            return;
        } 
        const studentsList = brigade.students.join(', ');
        
        html += `
            <div class="row">
                <div class="col3">
                    ${brigade.num}
                </div>
                <div class="col3">
                    ${submit.lab_num}
                </div>
                <div class="col3">
                    ${submit.submission_date}
                </div>
                <div class="col3">
                    ${studentsList}
                </div>
            </div>
        `;
    });
    return html;
}

document.getElementById('pass-lab-form').addEventListener('submit', function(event) {
    event.preventDefault(); 

    const formData = new FormData(event.target);

    const jsonData = {};
    formData.forEach((value, key) => {
        jsonData[key] = value;
    });

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${baseUrl}/labs/submit`, false);
    xhr.setRequestHeader('Content-Type', 'application/json');

    try {
        xhr.send(JSON.stringify(jsonData));
        if (xhr.status == 200) {
            const response = JSON.parse(xhr.responseText);
            console.log('Success:', response);
            
        } else {
            const response = JSON.parse(xhr.responseText);
            alert(response.detail);
        }
    } catch (error) {
        console.error('Request failed:', error);
    }

    loadAll();
});

document.getElementById('search-input').addEventListener('input', function(event) {
    loadAll(event.target.value);
})

loadAll()
document.getElementById("brigades-form").addEventListener('submit', createBrigade)