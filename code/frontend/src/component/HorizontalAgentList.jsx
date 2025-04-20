// src/component/HorizontalAgentList.jsx
import React from 'react';
import SmallAgentCard from './smallAgentCard';

const HorizontalAgentList = ({ agents = [] }) => {
  const scrollStyle = {
    /* 关键点 */
    overflowX: 'auto',      // 横向滚动
    overflowY: 'hidden',
    whiteSpace: 'nowrap',   // 子元素排成一行
    width: '100%',          // 占满父容器，避免 70% 那种残缺
    paddingBottom: '8px',   // 让出滚动条位置
    scrollbarGutter: 'stable', // Chrome 新属性，滚动条位置更稳
  };

  /* 自定义滚动条（可要可不要） */
  const webkitScrollbar = `
    .horizontal-scroll::-webkit-scrollbar { height: 8px; }
    .horizontal-scroll::-webkit-scrollbar-track { background:#f0f0f0;border-radius:4px; }
    .horizontal-scroll::-webkit-scrollbar-thumb { background:#ccc;border-radius:4px;border:2px solid #f0f0f0; }
    .horizontal-scroll::-webkit-scrollbar-thumb:hover { background:#aaa; }
  `;

  return (
    <>
      <style>{webkitScrollbar}</style>

      <div className="horizontal-scroll" style={scrollStyle}>
        {agents.map(a => (
          <SmallAgentCard
            key={a.id}
            agent={a}
            /* inline‑block + 固定/最小宽度 */
            style={{
              display: 'inline-block',
              verticalAlign: 'top',
              minWidth: 180,      // 你卡片大概多宽就写多少
              marginRight: 12,    // 卡片间距
            }}
          />
        ))}
      </div>
    </>
  );
};

export default HorizontalAgentList;
