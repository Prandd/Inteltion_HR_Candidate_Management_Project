import type { ReactNode } from "react";

interface Props {
    title:string;
    children:ReactNode;
}

function SectionCard({title,children}:Props){
    return (
        <section className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <h2 className="text-base font-semibold text-gray-900 mb-5">
                {title}
            </h2>
            {children}
        </section>
    );
}

export default SectionCard;