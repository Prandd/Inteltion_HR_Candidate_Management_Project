import type {
    CandidateDetailType
} from "../../types/candidate";


interface Props {

    candidate: CandidateDetailType;

}



function ContactSection({

    candidate

}: Props){


    return (

        <section

            className="
            bg-white
            border
            border-gray-200
            rounded-2xl
            p-5
            shadow-sm
            "

        >


            <h2

                className="
                text-base
                font-semibold
                text-gray-900
                mb-5
                "

            >

                Contact

            </h2>



            <div

                className="
                space-y-5
                "

            >


                <ContactItem

                    icon="✉"

                    label="Email"

                    value={
                        candidate.email || "-"
                    }

                    href={
                        candidate.email
                        ?
                        `mailto:${candidate.email}`
                        :
                        undefined
                    }

                />



                <ContactItem

                    icon="☎"

                    label="Phone"

                    value={
                        candidate.phone || "-"
                    }

                    href={
                        candidate.phone
                        ?
                        `tel:${candidate.phone}`
                        :
                        undefined
                    }

                />


            </div>


        </section>

    );

}





interface ContactItemProps {

    icon:string;

    label:string;

    value:string;

    href?:string;

}





function ContactItem({

    icon,

    label,

    value,

    href

}:ContactItemProps){


    return (

        <div

            className="
            flex
            items-start
            gap-3
            "

        >


            {/* Icon */}

            <div

                className="
                w-9
                h-9
                rounded-xl
                bg-blue-50
                text-blue-600
                flex
                items-center
                justify-center
                text-sm
                flex-shrink-0
                "

            >

                {icon}

            </div>




            {/* Content */}

            <div

                className="
                min-w-0
                "

            >


                <p

                    className="
                    text-xs
                    text-gray-400
                    "

                >

                    {label}

                </p>



                {
                    href

                    ?

                    <a

                        href={href}

                        className="
                        text-sm
                        font-medium
                        text-gray-800
                        mt-1
                        block
                        hover:text-blue-600
                        transition
                        cursor-pointer
                        break-all
                        "

                    >

                        {value}

                    </a>


                    :


                    <p

                        className="
                        text-sm
                        font-medium
                        text-gray-800
                        mt-1
                        "

                    >

                        {value}

                    </p>

                }



            </div>


        </div>

    );

}



export default ContactSection;