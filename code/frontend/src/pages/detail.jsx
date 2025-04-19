const Detail = () => {
    return (
        <div>
            <div className="agent-detail">
                <h2>Agent Name</h2>
                <p>Description of the agent goes here. This agent specializes in...</p>
                <div className="agent-info">
                    <p><strong>Category:</strong> AI Agent Category</p>
                    <p><strong>Rating:</strong> ★★★★☆</p>
                    <p><strong>Price:</strong> $XX.XX per hour</p>
                </div>
            </div>
            <div className="reviews-section">
                <h3>Reviews</h3>
                <div className="review">
                    <p><strong>Review 1:</strong> content</p>
                </div>
            </div>
        </div>
    );
}

export default Detail;