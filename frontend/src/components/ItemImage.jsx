import React, { useState } from 'react';

const PLACEHOLDER_SRC = 'data:image/svg+xml,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" fill="none">' +
  '<rect width="200" height="200" fill="#f4f4f5"/>' +
  '<text x="50%" y="50%" text-anchor="middle" dy=".3em" font-family="system-ui" font-size="14" fill="#a1a1aa">No image</text>' +
  '</svg>'
);

function ItemImage({ src, alt, className, fallbackColor }) {
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    if (fallbackColor) {
      return (
        <div
          className={className}
          style={{ backgroundColor: fallbackColor }}
          role="img"
          aria-label={alt || 'Clothing item'}
        />
      );
    }
    return (
      <img
        src={PLACEHOLDER_SRC}
        alt={alt || 'No image available'}
        className={className}
      />
    );
  }

  return (
    <img
      src={src}
      alt={alt || 'Clothing item'}
      className={className}
      onError={() => setFailed(true)}
    />
  );
}

export default ItemImage;
