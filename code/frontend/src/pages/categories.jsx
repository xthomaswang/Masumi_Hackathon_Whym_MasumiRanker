import Agents from "../component/agents";

const Categories = () => {
    return (
      <div>
        {/* 分类标签 */}
        <div id="categories-container">
          {["Category Name", "Category Name", "Category Name"].map((cat, i) => (
            <div key={i} className="categories-tag">
              <span>{cat}</span>
            </div>
          ))}
        </div>
  
        {/* 推荐 agent 列表 */}
        <div className="recommended-agents">
          <h3>Hottest AI Agents</h3>
          <Agents />
        </div>
      </div>
    );
  };
  
  export default Categories;
  