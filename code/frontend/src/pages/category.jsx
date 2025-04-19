import { useParams } from "react-router-dom";
import Agents from "../component/agents";

const Category = () => {
  const { tag } = useParams();

  return (
    <div className="category-page">
      <h1 className="category-title">
        Category: {decodeURIComponent(tag).replace(/-/g, ' ')}
      </h1>
      
      <p className="category-description">
        Description of the category goes here. This category includes agents that specialize in {decodeURIComponent(tag).replace(/-/g, ' ')}.
      </p>

      <h3 className="category-subheading">Top Recommended Agents</h3>
      
      <div className="agents-container">
        <Agents />
      </div>
    </div>
  );
};

export default Category;
