const Agents = () => {
    return (
        <div className="agents-container">
            <div className="agent-card">
              <div className="agent-left">
                <div className="img">
                  <img src="/image/images.jpeg" alt="agent icon" />
                </div>
                <div className="agent-info">
                  <h4>Agent Name</h4>
                  <p>Short description of the agent.</p>
                </div>
              </div>
  
              <div className="star-price-section">
                <div className="star-rate"><span>★★★★☆</span></div>
                <div className="price"><span>$XX.XX</span></div>
              </div>
            </div>
        </div>
    )
}

export default Agents;