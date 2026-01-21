import { useState, useRef } from 'react'
import './App.css'

function App() {
  const [url, setUrl] = useState('')
  const [startYear, setStartYear] = useState(2015)
  const [endYear, setEndYear] = useState(2018)
  const [status, setStatus] = useState('idle')
  const [videoUrl, setVideoUrl] = useState(null)
  const [message, setMessage] = useState('')

  const pollingRef = useRef(null)

  const checkVideoAvailability = async (filename) => {
    try {
      const response = await fetch(`http://localhost:8001/check-video/${filename}`)
      const data = await response.json()

      if (data.ready === true) {
        clearInterval(pollingRef.current)
        setStatus('success')
        setMessage('Video Created!')
      }
    } catch (err) {
      console.log("Error Communicating With Server!", err)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (pollingRef.current) clearInterval(pollingRef.current)
    setStatus('loading')
    setMessage('Sending Request To Server!')
    setVideoUrl(null)

    try {
      const response = await fetch('http://localhost:8001/create-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: url,
          start_year: parseInt(startYear),
          end_year: parseInt(endYear)
        }),
      })

      if (!response.ok) throw new Error('Error Reaching The Server!')

      const data = await response.json()
      
      setVideoUrl(data.video_url)
      setStatus('processing')
      setMessage('Video Is Being Generated In The Background!')

      pollingRef.current = setInterval(() => {
        checkVideoAvailability(data.video_filename) 
      }, 3000)
      
    } catch (error) {
      console.error(error)
      setStatus('error')
      setMessage('Error: ' + error.message)
    }
  }

  return (
    <div className="container">
      <h1>Wayback Time Machine</h1>
      <p className="subtitle">With this tool you can create videos of different websites displaying the development of them throughout the years!</p>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Website URL:</label>
            <input
              type="text"
              placeholder="eg. https://google.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
          </div>

          <div className="row">
            <div className="form-group">
              <label>Start Year</label>
              <input
                type="number"
                value={startYear}
                onChange={(e) => setStartYear(e.target.value)}
                min="1995" max="2024"
              />
            </div>
            <div className="form-group">
              <label>End Year</label>
              <input
                type="number"
                value={endYear}
                onChange={(e) => setEndYear(e.target.value)}
                min="1995" max="2024"
              />
            </div>
          </div>

          <button type="submit" disabled={status === 'loading' || status === 'processing'}>
            {status === 'loading' ? 'Starting...' :
              status === 'processing' ? 'Generating Video... (Might take a few minutes)' :
                'Generate Video'}
          </button>
        </form>

        {message && (
          <div className={`message ${status}`}>
            {message}
          </div>
        )}

        {status === 'success' && videoUrl && (
          <div className="result-area">
            <a href={videoUrl} target="_blank" className="download-link">
              Open Video In New Tab
            </a>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
