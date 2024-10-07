'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Home() {
  const [field, setField] = useState({ name: '', dataType: '', description: '' });
  const [documentText, setDocumentText] = useState('');
  const [result, setResult] = useState(null);
  const [payload, setPayload] = useState({ document_text: '', fields: [] });

  const handleInputChange = (event) => {
    const { name, value } = event.target;
    setField((prevField) => ({ ...prevField, [name]: value }));
  };

  const handleDocumentTextChange = (e) => {
    setDocumentText(e.target.value);
  };

  const convertToSnakeCase = (field) => ({
    name: field.name,
    data_type: field.dataType,
    description: field.description
  });

  useEffect(() => {
    const snakeCasedField = convertToSnakeCase(field);
    setPayload({
      document_text: documentText,
      fields: [snakeCasedField],
    });
  }, [field, documentText]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResult(null);
    try {
      const response = await axios.post('http://localhost:8001/extract', payload);
      setResult(response.data);  // Set result  after the response

    } catch (err) {
      console.error('Error:', err);
    }
  };

  const extractedData = () => {
    return (
      <div>
        <h1>Extracted Data</h1>
        <table style={{ width: "100%", border: "1px solid black", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ border: "1px solid black", padding: "8px" }}>Extracted Data</th>
              <th style={{ border: "1px solid black", padding: "8px" }}>Reference</th>
            </tr>
          </thead>
          <tbody>
            {result?.extracted_values?.map((item, index) => (
              <tr key={index}>
                <td style={{ border: "1px solid black", padding: "8px" }}>{item?.value}</td>
                <td style={{ border: "1px solid black", padding: "8px" }}>{item?.reference}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="center">
      <h1>Document Extraction</h1>
      <form onSubmit={handleSubmit} className="form-area">
        <div className="fields">
          <input
            type="text"
            name="name"
            placeholder="Name"
            value={field.name}
            onChange={handleInputChange}
            required
          />
          <input
            type="text"
            name="dataType"
            placeholder="Data Type"
            value={field.dataType}
            onChange={handleInputChange}
            required
          />
          <input
            type="text"
            name="description"
            placeholder="Description"
            value={field.description}
            onChange={handleInputChange}
            required
          />
        </div>
        <textarea
          placeholder="Enter document text here"
          value={documentText}
          onChange={handleDocumentTextChange}
          required
        />
        <button type="submit" className="submit-btn">Submit</button>
      </form>

{result && Array.isArray(result.extracted_values) ? (
      result.extracted_values.length !== 0 ? (
        extractedData() // Call of function to show the output in a tabular way
      ) : (
        <h3>No data found</h3> // If no output then display this message
      )
    ) : null}
        </div>
  );
}







//dkkdkdk