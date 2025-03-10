from flask import Flask, request, jsonify, render_template
from opencorporates_agent import OpenCorporatesAgent
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize the OpenCorporates agent
agent = OpenCorporatesAgent()

@app.route('/')
def index():
    """Render the main page with search form"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_company():
    """API endpoint to search for company information"""
    data = request.json
    company_name = data.get('company_name')
    jurisdiction = data.get('jurisdiction')
    
    if not company_name:
        return jsonify({'error': 'Company name is required'}), 400
    
    result = agent.find_company_controllers(company_name, jurisdiction)
    return jsonify(result)

@app.route('/api/company_details', methods=['GET'])
def get_company_details():
    """API endpoint to get detailed company information"""
    jurisdiction = request.args.get('jurisdiction')
    company_number = request.args.get('company_number')
    
    if not jurisdiction or not company_number:
        return jsonify({'error': 'Jurisdiction and company number are required'}), 400
    
    company = agent.get_company_details(jurisdiction, company_number)
    officers = agent.get_company_officers(jurisdiction, company_number)
    
    return jsonify({
        'company': company,
        'officers': officers
    })

# HTML templates (for a real application, these would be in separate files)
@app.route('/templates/index.html')
def get_index_template():
    """Provide the HTML template for the main page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OpenCorporates Company Lookup</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-100">
        <div class="container mx-auto p-4">
            <h1 class="text-2xl font-bold mb-4">Company Controller Lookup</h1>
            
            <div class="bg-white p-6 rounded-lg shadow-md">
                <div class="mb-4">
                    <label for="company_name" class="block text-gray-700 font-bold mb-2">Company Name:</label>
                    <input type="text" id="company_name" class="w-full p-2 border rounded" placeholder="Enter company name, e.g., HOMECOMERS RCC INC">
                </div>
                
                <div class="mb-4">
                    <label for="jurisdiction" class="block text-gray-700 font-bold mb-2">Jurisdiction (optional):</label>
                    <input type="text" id="jurisdiction" class="w-full p-2 border rounded" placeholder="E.g., CA, Illinois, etc.">
                </div>
                
                <button id="search_button" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                    Search
                </button>
            </div>
            
            <div id="loading" class="mt-4 text-center hidden">
                <p class="text-gray-700">Searching OpenCorporates database...</p>
            </div>
            
            <div id="results" class="mt-4 hidden">
                <h2 class="text-xl font-bold mb-2">Results</h2>
                <div id="results_content" class="bg-white p-6 rounded-lg shadow-md"></div>
            </div>
            
            <div id="error" class="mt-4 hidden">
                <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4" role="alert">
                    <p id="error_message"></p>
                </div>
            </div>
        </div>
        
        <script>
            document.getElementById('search_button').addEventListener('click', async function() {
                const companyName = document.getElementById('company_name').value.trim();
                const jurisdiction = document.getElementById('jurisdiction').value.trim();
                
                if (!companyName) {
                    showError('Please enter a company name');
                    return;
                }
                
                showLoading();
                
                try {
                    const response = await fetch('/api/search', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            company_name: companyName,
                            jurisdiction: jurisdiction
                        }),
                    });
                    
                    const data = await response.json();
                    
                    hideLoading();
                    
                    if (data.error) {
                        showError(data.error);
                    } else {
                        showResults(data);
                    }
                } catch (error) {
                    hideLoading();
                    showError('An error occurred while fetching data');
                    console.error(error);
                }
            });
            
            function showLoading() {
                document.getElementById('loading').classList.remove('hidden');
                document.getElementById('results').classList.add('hidden');
                document.getElementById('error').classList.add('hidden');
            }
            
            function hideLoading() {
                document.getElementById('loading').classList.add('hidden');
            }
            
            function showError(message) {
                const errorDiv = document.getElementById('error');
                document.getElementById('error_message').textContent = message;
                errorDiv.classList.remove('hidden');
                document.getElementById('results').classList.add('hidden');
            }
            
            function showResults(data) {
                const resultsDiv = document.getElementById('results');
                const resultsContent = document.getElementById('results_content');
                
                let html = '';
                
                if (data.status === 'not_found') {
                    html = `<p class="text-gray-700">${data.message}</p>`;
                } else {
                    html = `<p class="mb-4">${data.message}</p>`;
                    
                    data.results.forEach(company => {
                        html += `
                            <div class="border-b pb-4 mb-4">
                                <h3 class="text-lg font-bold">${company.company_name}</h3>
                                <p class="text-sm text-gray-600">
                                    Jurisdiction: ${company.jurisdiction}, 
                                    Company Number: ${company.company_number}
                                </p>
                                <p class="text-sm text-gray-600">
                                    Incorporation Date: ${company.incorporation_date || 'N/A'},
                                    Status: ${company.current_status || 'N/A'}
                                </p>
                                
                                <h4 class="font-bold mt-2">Officers/Controllers:</h4>
                                <ul class="list-disc pl-5">
                        `;
                        
                        if (company.officers && company.officers.length > 0) {
                            company.officers.forEach(officer => {
                                const officerData = officer.officer || {};
                                html += `
                                    <li>
                                        <strong>${officerData.name || 'Unknown'}</strong> 
                                        (Position: ${officerData.position || 'Unknown'})
                                        ${officerData.start_date ? `Since: ${officerData.start_date}` : ''}
                                    </li>
                                `;
                            });
                        } else {
                            html += `<li>No officer information available</li>`;
                        }
                        
                        html += `
                                </ul>
                            </div>
                        `;
                    });
                }
                
                resultsContent.innerHTML = html;
                resultsDiv.classList.remove('hidden');
            }
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
